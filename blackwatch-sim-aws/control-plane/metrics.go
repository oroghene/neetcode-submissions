package main

// Observability sidecar for the control plane: a Prometheus-style text
// endpoint (/metrics), a JSON fleet API (/api/fleet), and a small operator
// dashboard (/dashboard) that polls it. In production these map to the
// CloudWatch agent scraping /metrics and a CloudWatch dashboard; the CDK
// stack in cdk/ defines that side.

import (
	_ "embed"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sort"
	"strings"
	"sync/atomic"
	"time"
)

//go:embed dashboard.html
var dashboardHTML []byte

type counters struct {
	mitigationsPlaced atomic.Int64
	configPushes      atomic.Int64
	drains            atomic.Int64
	healthReports     atomic.Int64
}

type fleetHostJSON struct {
	HostID                string  `json:"hostId"`
	Pop                   string  `json:"pop"`
	Connected             bool    `json:"connected"`
	Draining              bool    `json:"draining"`
	ActiveMitigations     int32   `json:"activeMitigations"`
	LargestFreeBlockBytes int64   `json:"largestFreeBlockBytes"`
	CPUPct                float64 `json:"cpuPct"`
	LastConfigLoadMs      int64   `json:"lastConfigLoadMs"`
	HeartbeatAgeS         float64 `json:"heartbeatAgeS"`
}

type fleetJSON struct {
	Hosts             []fleetHostJSON `json:"hosts"`
	ActiveMitigations int             `json:"activeMitigations"`
	MitigationsPlaced int64           `json:"mitigationsPlaced"`
	ConfigPushes      int64           `json:"configPushes"`
	Drains            int64           `json:"drains"`
	HealthReports     int64           `json:"healthReports"`
}

func (s *server) fleetSnapshot() fleetJSON {
	s.mu.Lock()
	defer s.mu.Unlock()
	now := time.Now().UnixMilli()
	out := fleetJSON{
		ActiveMitigations: len(s.mitigations),
		MitigationsPlaced: s.counters.mitigationsPlaced.Load(),
		ConfigPushes:      s.counters.configPushes.Load(),
		Drains:            s.counters.drains.Load(),
		HealthReports:     s.counters.healthReports.Load(),
	}
	for _, h := range s.hosts {
		row := fleetHostJSON{
			Pop:       h.info.GetPop(),
			HostID:    h.info.GetHostId(),
			Connected: h.connected,
			Draining:  h.draining,
		}
		if lh := h.lastHealth; lh != nil {
			row.ActiveMitigations = lh.ActiveMitigations
			row.LargestFreeBlockBytes = lh.LargestFreeBlockBytes
			row.CPUPct = lh.CpuPct
			row.LastConfigLoadMs = lh.LastConfigLoadMs
			row.HeartbeatAgeS = float64(now-lh.ReportedAtUnixMs) / 1000
		}
		out.Hosts = append(out.Hosts, row)
	}
	sort.Slice(out.Hosts, func(i, j int) bool { return out.Hosts[i].HostID < out.Hosts[j].HostID })
	return out
}

func (s *server) renderPrometheus() string {
	snap := s.fleetSnapshot()
	var b strings.Builder
	emit := func(name, help, typ string, value any) {
		fmt.Fprintf(&b, "# HELP %s %s\n# TYPE %s %s\n%s %v\n", name, help, name, typ, name, value)
	}
	connected := 0
	for _, h := range snap.Hosts {
		if h.Connected {
			connected++
		}
	}
	emit("bwsim_hosts_connected", "Hosts with an open push stream", "gauge", connected)
	emit("bwsim_hosts_total", "Registered hosts", "gauge", len(snap.Hosts))
	emit("bwsim_mitigations_active", "Currently active mitigations", "gauge", snap.ActiveMitigations)
	emit("bwsim_mitigations_placed_total", "Mitigations placed since start", "counter", snap.MitigationsPlaced)
	emit("bwsim_config_pushes_total", "Config messages pushed to hosts", "counter", snap.ConfigPushes)
	emit("bwsim_drains_total", "Drain commands issued", "counter", snap.Drains)
	emit("bwsim_health_reports_total", "Health reports ingested", "counter", snap.HealthReports)

	fmt.Fprintf(&b, "# HELP bwsim_host_largest_free_block_bytes Fragmentation early-warning per host\n# TYPE bwsim_host_largest_free_block_bytes gauge\n")
	for _, h := range snap.Hosts {
		fmt.Fprintf(&b, "bwsim_host_largest_free_block_bytes{host_id=%q,pop=%q} %d\n", h.HostID, h.Pop, h.LargestFreeBlockBytes)
	}
	fmt.Fprintf(&b, "# HELP bwsim_host_config_load_ms Last mitigation load time per host\n# TYPE bwsim_host_config_load_ms gauge\n")
	for _, h := range snap.Hosts {
		fmt.Fprintf(&b, "bwsim_host_config_load_ms{host_id=%q,pop=%q} %d\n", h.HostID, h.Pop, h.LastConfigLoadMs)
	}
	return b.String()
}

func (s *server) serveMetrics(addr string) {
	mux := http.NewServeMux()
	mux.HandleFunc("/metrics", func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "text/plain; version=0.0.4")
		fmt.Fprint(w, s.renderPrometheus())
	})
	mux.HandleFunc("/api/fleet", func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("Access-Control-Allow-Origin", "*")
		_ = json.NewEncoder(w).Encode(s.fleetSnapshot())
	})
	mux.HandleFunc("/dashboard", func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		_, _ = w.Write(dashboardHTML)
	})
	log.Printf("metrics/dashboard listening on %s (/metrics /api/fleet /dashboard)", addr)
	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatalf("metrics server: %v", err)
	}
}
