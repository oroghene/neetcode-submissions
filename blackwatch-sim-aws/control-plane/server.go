package main

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	bwsimv1 "blackwatch-sim/control-plane/gen/bwsimv1"
)

type hostState struct {
	info       *bwsimv1.HostInfo
	lastHealth *bwsimv1.HealthReport
	push       chan *bwsimv1.PushMessage
	epoch      int64
	connected  bool
	draining   bool
}

type server struct {
	bwsimv1.UnimplementedMitigationServiceServer

	mu          sync.Mutex
	hosts       map[string]*hostState
	mitigations map[string]*bwsimv1.MitigationConfig
	version     int64
}

func newServer() *server {
	return &server{
		hosts:       make(map[string]*hostState),
		mitigations: make(map[string]*bwsimv1.MitigationConfig),
	}
}

func (s *server) RegisterHost(_ context.Context, info *bwsimv1.HostInfo) (*bwsimv1.RegisterAck, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	h, ok := s.hosts[info.HostId]
	if !ok {
		h = &hostState{}
		s.hosts[info.HostId] = h
	}
	h.info = info
	h.epoch++
	h.draining = false
	log.Printf("registered host=%s pop=%s epoch=%d", info.HostId, info.Pop, h.epoch)
	return &bwsimv1.RegisterAck{Ok: true, StreamEpoch: h.epoch}, nil
}

// StreamMitigations replays all active mitigations to a newly connected host,
// then pushes deltas until the host disconnects or is drained.
func (s *server) StreamMitigations(req *bwsimv1.StreamRequest, stream bwsimv1.MitigationService_StreamMitigationsServer) error {
	s.mu.Lock()
	h, ok := s.hosts[req.HostId]
	if !ok {
		s.mu.Unlock()
		return fmt.Errorf("host %s not registered", req.HostId)
	}
	ch := make(chan *bwsimv1.PushMessage, 64)
	h.push = ch
	h.connected = true
	backlog := make([]*bwsimv1.MitigationConfig, 0, len(s.mitigations))
	for _, m := range s.mitigations {
		backlog = append(backlog, m)
	}
	s.mu.Unlock()

	for _, m := range backlog {
		if err := stream.Send(&bwsimv1.PushMessage{Payload: &bwsimv1.PushMessage_Mitigation{Mitigation: m}}); err != nil {
			s.disconnect(req.HostId, ch)
			return err
		}
	}

	for {
		select {
		case <-stream.Context().Done():
			s.disconnect(req.HostId, ch)
			return nil
		case msg := <-ch:
			if err := stream.Send(msg); err != nil {
				s.disconnect(req.HostId, ch)
				return err
			}
			if msg.GetReboot() != nil {
				// Reboot command is the last message on the stream.
				s.disconnect(req.HostId, ch)
				return nil
			}
		}
	}
}

func (s *server) disconnect(hostID string, ch chan *bwsimv1.PushMessage) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if h, ok := s.hosts[hostID]; ok && h.push == ch {
		h.connected = false
		h.push = nil
	}
}

func (s *server) ReportHealth(_ context.Context, r *bwsimv1.HealthReport) (*bwsimv1.Ack, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	h, ok := s.hosts[r.HostId]
	if !ok {
		return &bwsimv1.Ack{Ok: false, Message: "unknown host"}, nil
	}
	h.lastHealth = r
	return &bwsimv1.Ack{Ok: true}, nil
}

func (s *server) PlaceMitigation(_ context.Context, req *bwsimv1.PlaceMitigationRequest) (*bwsimv1.Ack, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	m := req.Config
	s.version++
	m.Version = s.version
	m.PlacedAtUnixMs = time.Now().UnixMilli()
	s.mitigations[m.MitigationId] = m
	n := 0
	for _, h := range s.hosts {
		if h.connected && h.push != nil && !h.draining {
			select {
			case h.push <- &bwsimv1.PushMessage{Payload: &bwsimv1.PushMessage_Mitigation{Mitigation: m}}:
				n++
			default:
				log.Printf("push buffer full for host, dropping (host will resync on reconnect)")
			}
		}
	}
	log.Printf("placed mitigation=%s action=%s cidr=%s -> pushed to %d hosts", m.MitigationId, m.Action, m.TargetCidr, n)
	return &bwsimv1.Ack{Ok: true, Message: fmt.Sprintf("pushed to %d hosts", n)}, nil
}

func (s *server) ListFleet(context.Context, *bwsimv1.Empty) (*bwsimv1.FleetStatus, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	out := &bwsimv1.FleetStatus{}
	for _, h := range s.hosts {
		out.Hosts = append(out.Hosts, &bwsimv1.HostStatus{
			Info:       h.info,
			LastHealth: h.lastHealth,
			Connected:  h.connected,
			Draining:   h.draining,
		})
	}
	return out, nil
}

func (s *server) DrainHost(_ context.Context, req *bwsimv1.DrainRequest) (*bwsimv1.Ack, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	h, ok := s.hosts[req.HostId]
	if !ok {
		return &bwsimv1.Ack{Ok: false, Message: "unknown host"}, nil
	}
	if !h.connected || h.push == nil {
		return &bwsimv1.Ack{Ok: false, Message: "host not connected"}, nil
	}
	h.draining = true
	h.push <- &bwsimv1.PushMessage{Payload: &bwsimv1.PushMessage_Reboot{Reboot: &bwsimv1.RebootCommand{
		Reason:       req.Reason,
		DrainSeconds: 2,
	}}}
	log.Printf("drain issued host=%s reason=%q", req.HostId, req.Reason)
	return &bwsimv1.Ack{Ok: true}, nil
}
