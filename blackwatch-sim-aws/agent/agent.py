"""Host diagnostics agent for the scrubbing-fleet simulation.

Runs on each (simulated) scrubbing host:
  - registers with the control plane and opens the mitigation push stream
  - "loads" each mitigation into a simulated dataplane memory pool, measuring
    load time against the configured load SLA
  - reports health every HEALTH_INTERVAL_S, including the fragmentation
    early-warning metric `largest_free_block_bytes`
  - honors reboot/drain commands: stops taking configs, drains, re-registers

Simulated hosts never touch real traffic; the "dataplane" is a dict.
"""

import argparse
import random
import sys
import threading
import time

import grpc

sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/gen/python")
import bwsim_pb2 as pb
import bwsim_pb2_grpc as rpc

HEALTH_INTERVAL_S = 2
LOAD_SLA_MS = 30_000
POOL_BYTES = 8 * 1024**3  # simulated dataplane memory pool


class Dataplane:
    """Toy model of mitigation filter memory (think: bloom filters, IPSets)."""

    def __init__(self, leak: bool):
        self.mitigations: dict[str, int] = {}  # id -> bytes allocated
        self.leak = leak
        self.wasted = 0  # bytes lost to fragmentation, grows on leaky hosts

    def load(self, m: pb.MitigationConfig) -> int:
        start = time.monotonic()
        # Filter structures cost 200-400MB depending on rule complexity.
        cost = random.randint(200, 400) * 1024**2
        self.mitigations[m.mitigation_id] = cost
        if self.leak:
            self.wasted += random.randint(2000, 2600) * 1024**2
        time.sleep(random.uniform(0.05, 0.25))  # simulated load work
        return int((time.monotonic() - start) * 1000)

    def used(self) -> int:
        return sum(self.mitigations.values()) + self.wasted

    def largest_free_block(self) -> int:
        free = max(POOL_BYTES - self.used(), 0)
        # Fragmentation model: contiguity degrades as more filters are packed in.
        return int(free / (1 + len(self.mitigations) / 2))


class Agent:
    def __init__(self, host_id: str, pop: str, target: str, leak: bool):
        self.host_id = host_id
        self.pop = pop
        self.target = target
        self.dp = Dataplane(leak)
        self.last_load_ms = 0
        self.running = True
        self.rebooting = threading.Event()

    def log(self, msg: str):
        print(f"[{self.host_id}] {msg}", flush=True)

    def run(self):
        while self.running:
            try:
                self.session()
            except grpc.RpcError as e:
                self.log(f"stream lost ({e.code().name}), reconnecting in 1s")
                time.sleep(1)

    def session(self):
        with grpc.insecure_channel(self.target) as channel:
            stub = rpc.MitigationServiceStub(channel)
            ack = stub.RegisterHost(
                pb.HostInfo(host_id=self.host_id, pop=self.pop, capacity_gbps=100)
            )
            self.log(f"registered, epoch={ack.stream_epoch}")
            self.rebooting.clear()

            reporter = threading.Thread(
                target=self.report_health, args=(stub,), daemon=True
            )
            reporter.start()

            for msg in stub.StreamMitigations(pb.StreamRequest(host_id=self.host_id)):
                if msg.HasField("mitigation"):
                    m = msg.mitigation
                    self.last_load_ms = self.dp.load(m)
                    sla = "OK" if self.last_load_ms <= LOAD_SLA_MS else "VIOLATION"
                    self.log(
                        f"loaded {m.mitigation_id} action={pb.Action.Name(m.action)} "
                        f"cidr={m.target_cidr} in {self.last_load_ms}ms (SLA {sla}) "
                        f"largest_free_block={self.dp.largest_free_block() // 1024**2}MB"
                    )
                elif msg.HasField("reboot"):
                    self.reboot(msg.reboot)
                    return

    def reboot(self, cmd: pb.RebootCommand):
        self.rebooting.set()
        self.log(f"REBOOT commanded (reason={cmd.reason!r}); draining {cmd.drain_seconds}s")
        time.sleep(cmd.drain_seconds)
        self.dp = Dataplane(leak=False)  # fresh boot clears fragmentation
        self.log("rebooted, memory pool reset; re-registering")

    def report_health(self, stub):
        while not self.rebooting.is_set():
            try:
                stub.ReportHealth(
                    pb.HealthReport(
                        host_id=self.host_id,
                        cpu_pct=random.uniform(20, 60),
                        memory_used_bytes=self.dp.used(),
                        largest_free_block_bytes=self.dp.largest_free_block(),
                        active_mitigations=len(self.dp.mitigations),
                        last_config_load_ms=self.last_load_ms,
                        reported_at_unix_ms=int(time.time() * 1000),
                    )
                )
            except grpc.RpcError:
                return
            time.sleep(HEALTH_INTERVAL_S)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host-id", required=True)
    ap.add_argument("--pop", default="iad-edge-1")
    ap.add_argument("--target", default="localhost:50061")
    ap.add_argument(
        "--leak",
        action="store_true",
        help="simulate dataplane memory fragmentation so the orchestrator reboots us",
    )
    args = ap.parse_args()
    Agent(args.host_id, args.pop, args.target, args.leak).run()


if __name__ == "__main__":
    main()
