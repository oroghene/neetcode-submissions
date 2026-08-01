// Control plane for the scrubbing-fleet simulation.
//
// Holds the fleet registry, pushes mitigation configs to connected hosts over
// server-streaming gRPC, ingests health reports, and exposes operator RPCs
// (place mitigation, list fleet, drain host) used by the CLI and the
// auto-reboot orchestrator.
package main

import (
	"flag"
	"log"
	"net"

	"google.golang.org/grpc"

	bwsimv1 "blackwatch-sim/control-plane/gen/bwsimv1"
)

func main() {
	addr := flag.String("addr", ":50061", "listen address")
	flag.Parse()

	lis, err := net.Listen("tcp", *addr)
	if err != nil {
		log.Fatalf("listen: %v", err)
	}
	s := grpc.NewServer()
	bwsimv1.RegisterMitigationServiceServer(s, newServer())
	log.Printf("control plane listening on %s", *addr)
	if err := s.Serve(lis); err != nil {
		log.Fatalf("serve: %v", err)
	}
}
