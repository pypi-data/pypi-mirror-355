from typing import List, Tuple, Dict, Union


class _dagNode:
    def __init__(self, name: str):
        self.name = name
        self.incoming_nodes: List["_dagNode"] = []
        self.outgoing_nodes: List["_dagNode"] = []

    def goto(self, *nodes: "_dagNode"):
        for node in nodes:
            self.outgoing_nodes.append(node)
            node.incoming_nodes.append(self)
        return self

    def arrives_from(self, *nodes: "_dagNode"):
        for node in nodes:
            node.outgoing_nodes.append(self)
            self.incoming_nodes.append(node)
        return self

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class _capsuleDeployerStateMachine:
    def __init__(self):
        # -- (your existing setup) --
        start_state = _dagNode("start")
        fail_state = _dagNode("fail")
        success_state = _dagNode("success")
        upgrade_state = _dagNode("upgrade")
        first_time_create_state = _dagNode("first_time_create")
        end_state = _dagNode("end")

        capsule_deploy_api_call = _dagNode("capsule_deploy_api_call")
        capsule_deploy_api_call_rejected = _dagNode("capsule_deploy_api_call_rejected")
        capsule_worker_pending = _dagNode("capsule_worker_pending")

        capsule_single_worker_ready = _dagNode("capsule_single_worker_ready")
        capsule_multiple_workers_ready = _dagNode("capsule_all_workers_ready")
        current_deployment_deployed_worker_crashed = _dagNode(
            "current_deployment_deployed_worker_crashed"
        )
        current_deployment_workers_pending_beyond_timeout = _dagNode(
            "current_deployment_workers_pending_beyond_timeout"
        )

        start_state.goto(first_time_create_state, upgrade_state)

        capsule_deploy_api_call.arrives_from(
            first_time_create_state, upgrade_state
        ).goto(capsule_deploy_api_call_rejected, capsule_worker_pending)

        capsule_worker_pending.goto(
            capsule_single_worker_ready,
            capsule_multiple_workers_ready,
            current_deployment_deployed_worker_crashed,
            current_deployment_workers_pending_beyond_timeout,
        )
        success_state.arrives_from(
            capsule_single_worker_ready, capsule_multiple_workers_ready
        ).goto(end_state)
        fail_state.arrives_from(
            capsule_deploy_api_call_rejected,
            current_deployment_deployed_worker_crashed,
            current_deployment_workers_pending_beyond_timeout,
        ).goto(end_state)

        self._states = [
            start_state,
            fail_state,
            success_state,
            upgrade_state,
            first_time_create_state,
            end_state,
            capsule_single_worker_ready,
            capsule_multiple_workers_ready,
            current_deployment_deployed_worker_crashed,
            current_deployment_workers_pending_beyond_timeout,
            capsule_deploy_api_call,
            capsule_deploy_api_call_rejected,
            capsule_worker_pending,
        ]

    def get_edges(self) -> List[Tuple["_dagNode", "_dagNode"]]:
        """
        Returns a list of (src_node, dst_node) tuples for all transitions.
        """
        edges = []
        for node in self._states:
            for out in node.outgoing_nodes:
                edges.append((node, out))
        return edges

    def to_dot(self, graph_name="StateMachine"):
        """
        Emit a Graphviz DOT description of the state machine.
        """
        lines = [f"digraph {graph_name} {{"]
        # optional: rankdir=LR for left-to-right layout
        lines.append("    rankdir=LR;")
        for src, dst in self.get_edges():
            lines.append(f'    "{src}" -> "{dst}";')
        lines.append("}")
        return "\n".join(lines)

    def adjacency_list(self):
        """
        Returns a dict mapping each node to list of its outgoing nodes.
        """
        return {node: list(node.outgoing_nodes) for node in self._states}

    def __str__(self):
        # Default to DOT format; you could swap this out for something else
        return self.to_dot()

    def to_diagraph(self):
        from graphviz import Digraph

        # Create a new Digraph
        dot = Digraph(name="StateMachine", format="png")
        dot.attr(rankdir="LR")  # left-to-right layout

        # Add one edge per transition in your SM
        for src, dst in self.get_edges():
            # src and dst are _dagNode instances; use their .name (or str(src))
            dot.edge(src.name, dst.name)

        # Render to file (e.g. "state_machine.png") and optionally view it:
        dot.render("state_machine", view=False)


from typing import TypedDict


class WorkerStatus(TypedDict):
    workerId: str
    phase: str
    activity: int
    activityDataAvailable: bool
    version: str


from typing import Dict, List, TypedDict


class WorkerInfoDict(TypedDict):
    # TODO : Check if we need to account for the `Terminating` state
    pending: Dict[str, List[WorkerStatus]]
    running: Dict[str, List[WorkerStatus]]
    crashlooping: Dict[str, List[WorkerStatus]]


class CurrentWorkerInfo(TypedDict):
    # TODO : Check if we need to account for the `Terminating` state
    pending: int
    running: int
    crashlooping: int


class DEPLOYMENT_READY_CONDITIONS:
    """
    Deployment ready conditions define what is considered a successful completion of a deployment.
    This allows users or platform designers to configure the criteria for deployment readiness.

    Reasons for different deployment modes include:
    1) [at_least_one_running] Some endpoints may be deployed ephemerally and are considered ready when at least one instance is running; additional instances are for load management.
    2) [all_running] Operators may require that all replicas are available, running, and only the current deployment version is serving traffic.
    3) [fully_finished] Operators may only care that the minimum number of replicas for the current rollout are present in the cluster.
    """

    # `ATLEAST_ONE_RUNNING` implies that atleast one worker of the current deployment instance's version has started running.
    ATLEAST_ONE_RUNNING = "at_least_one_running"

    # `ALL_RUNNING` implies that all workers of the current deployment instance's version have started running (i.e. all workers aligning to the minimum number of replicas).
    # It doesn't imply that all the workers relating to other deployments have been torn down.
    ALL_RUNNING = "all_running"

    # `FULLY_FINISHED` implies that the deployment has the minimum number of replicas and all the workers are related to the current deployment instance's version.
    FULLY_FINISHED = "fully_finished"

    @classmethod
    def docstring(cls):
        return cls.__doc__

    @classmethod
    def enums(cls):
        return [
            cls.ATLEAST_ONE_RUNNING,
            cls.ALL_RUNNING,
            cls.FULLY_FINISHED,
        ]


class CapsuleWorkerStatusDict(TypedDict):
    at_least_one_pending: bool
    at_least_one_running: bool
    at_least_one_crashlooping: bool
    all_running: bool
    fully_finished: bool
    none_present: bool
    current_info: CurrentWorkerInfo


class CapsuleWorkerSemanticStatus(TypedDict):
    final_version: str
    status: CapsuleWorkerStatusDict
    worker_info: WorkerInfoDict


def _capsule_worker_status_diff(
    current_status: CapsuleWorkerSemanticStatus,
    previous_status: Union[CapsuleWorkerSemanticStatus, None],
) -> List[str]:
    """
    The goal of this function is to return a status string that will be used to update the user the
    change in status of the different capsules.
    """
    if previous_status is None:
        # Check if the current status has pending workers or crashlooping workers
        curr = current_status["status"]["current_info"]
        version = current_status["final_version"]
        changes = []

        if curr["pending"] > 0:
            changes.append(f"⏳ {curr['pending']} worker(s) pending")

        if curr["running"] > 0:
            changes.append(f"🚀 {curr['running']} worker(s) currently running")

        if curr["crashlooping"] > 0:
            changes.append(f"💥 {curr['crashlooping']} worker(s) currently crashlooping")

        return changes

    curr = current_status["status"]["current_info"]
    prev = previous_status["status"]["current_info"]
    version = current_status["final_version"]

    changes = []

    # Track worker count changes for the target version
    pending_diff = curr["pending"] - prev["pending"]
    running_diff = curr["running"] - prev["running"]
    crash_diff = curr["crashlooping"] - prev["crashlooping"]

    # Worker count changes
    if pending_diff > 0:
        changes.append(
            f"⏳ {pending_diff} new worker(s) pending. Total pending ({curr['pending']})"
        )

    if running_diff > 0:
        changes.append(
            f"🚀 {running_diff} worker(s) started running. Total running ({curr['running']})"
        )
    elif running_diff < 0:
        changes.append(
            f"🛑 {abs(running_diff)} worker(s) stopped running. Total running ({curr['running']})"
        )

    if crash_diff > 0:
        changes.append(
            f"💥 {crash_diff} worker(s) started crashlooping. Total crashlooping ({curr['crashlooping']})"
        )
    elif crash_diff < 0:
        changes.append(f"🔧 {abs(crash_diff)} worker(s) recovered from crashlooping")

    # Significant state transitions
    if (
        not previous_status["status"]["at_least_one_running"]
        and current_status["status"]["at_least_one_running"]
    ):
        changes.append(f"✅ First worker came online")

    if (
        not previous_status["status"]["all_running"]
        and current_status["status"]["all_running"]
    ):
        changes.append(f"🎉 All workers are now running")

    if (
        not previous_status["status"]["at_least_one_crashlooping"]
        and current_status["status"]["at_least_one_crashlooping"]
    ):
        changes.append(f"⚠️  Worker crash detected")

    # Current state summary

    return changes


def _capsule_worker_semantic_status(
    workers: List[WorkerStatus], version: str, min_replicas: int
) -> CapsuleWorkerSemanticStatus:
    def _make_version_dict(
        _workers: List[WorkerStatus], phase: str
    ) -> Dict[str, List[WorkerStatus]]:
        xx: Dict[str, List[WorkerStatus]] = {}
        for w in _workers:
            if w.get("phase") != phase:
                continue
            if w.get("version") not in xx:
                xx[w.get("version")] = []
            xx[w.get("version")].append(w)
        return xx

    pending_workers = _make_version_dict(workers, "Pending")
    running_workers = _make_version_dict(workers, "Running")
    crashlooping_workers = _make_version_dict(workers, "CrashLoopBackOff")

    # current_status (formulated basis):
    # - atleast one pods are pending for `_end_state_capsule_version`
    # - atleast one pod is in Running state for `_end_state_capsule_version` (maybe terminal) [Might require heath-check thing here]
    # - alteast one pod is crashlooping for `_end_state_capsule_version` (maybe terminal)
    # - all pods are running for `_end_state_capsule_version` that match the minimum number of replicas
    # - all pods are running for `_end_state_capsule_version` that match the maximum number of replicas and no other pods of older versions are running
    # - no pods relating to `_end_state_capsule_version` are pending/running/crashlooping

    # Helper to count pods for the final version in each state
    def count_for_version(workers_dict):
        return len(workers_dict.get(version, []))

    status_dict: CapsuleWorkerStatusDict = {
        "at_least_one_pending": count_for_version(pending_workers) > 0,
        "at_least_one_running": count_for_version(running_workers) > 0,
        "at_least_one_crashlooping": count_for_version(crashlooping_workers) > 0,
        "none_present": (
            count_for_version(running_workers) == 0
            and count_for_version(pending_workers) == 0
            and count_for_version(crashlooping_workers) == 0
        ),
        "all_running": count_for_version(running_workers) == min_replicas,
        "fully_finished": count_for_version(running_workers) == min_replicas
        and len(pending_workers) == 0
        and len(crashlooping_workers) == 0,
        "current_info": {
            "pending": count_for_version(pending_workers),
            "running": count_for_version(running_workers),
            "crashlooping": count_for_version(crashlooping_workers),
        },
    }

    worker_info: WorkerInfoDict = {
        "pending": pending_workers,
        "running": running_workers,
        "crashlooping": crashlooping_workers,
    }

    return {
        "final_version": version,
        "status": status_dict,
        "worker_info": worker_info,
    }
