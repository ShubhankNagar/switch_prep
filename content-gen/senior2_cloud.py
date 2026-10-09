"""Subject 16: Cloud, Docker, Kubernetes & CI/CD (prefix cloud-)."""
from senior2_common import build, report, B, I, A

NOTES = []

NOTES.append(("cloud-aws-service-map", "AWS for Backend Engineers: The Service Map and When to Use What", r"""
You don't need to know 200 AWS services. Senior interviews check that you can pick the **right managed building block**, say why, and name its main limitation. Learn about 15 services well.

## The short list

| Need | Default choice | Pick something else when |
|---|---|---|
| Run a long-lived Spring Boot API | **ECS on Fargate** | You already run Kubernetes (EKS), or need GPUs/special hosts (EC2) |
| Event-driven, spiky, short jobs | **Lambda** | Work runs > 15 min, needs steady high throughput, or cold starts hurt your p99 |
| Relational data, transactions | **RDS MySQL/Postgres** or **Aurora** | Access patterns are simple key lookups at huge scale (DynamoDB) |
| Key-value at any scale | **DynamoDB** | You need ad-hoc queries, joins, reporting |
| Files, backups, data lake | **S3** | You need a POSIX filesystem (EFS) or block disk (EBS) |
| Queue for background work | **SQS** (Standard or FIFO) | You need replay or many consumer groups on one stream (Kafka/MSK, Kinesis) |
| Fan-out one event to many | **SNS** (often SNS to several SQS queues) or **EventBridge** | Strict ordering plus replay is required (MSK) |
| Cache / sessions / rate-limit counters | **ElastiCache** (Valkey/Redis) | Read-heavy DynamoDB tables only (DAX) |
| Static assets, edge caching | **CloudFront** in front of S3/ALB | Content is fully personalised and uncacheable |
| Load balancing HTTP | **ALB** | Raw TCP/UDP or static IPs (NLB) |
| Who can call what | **IAM** roles and policies | Never "something else"; it is everywhere |

## A typical Spring Boot deployment on AWS

```text
             Route 53 (DNS)
                  |
             CloudFront ---- S3 (Angular build, images)
                  |
         ALB (public subnets, TLS via ACM)
                  |
   ECS Fargate tasks / EKS pods (private subnets)
     |            |             |              |
 Aurora MySQL  ElastiCache    SQS queue ---> worker service
 (isolated)    (sessions,      |
               hot reads)     DLQ
                  |
      Secrets Manager, CloudWatch, X-Ray/OpenTelemetry
```

Be ready to explain each arrow: why the database is not reachable from the internet, why the worker reads from a queue instead of being called synchronously, where TLS terminates.

## Facts interviewers like to probe

- **S3** has had strong read-after-write consistency for all operations since December 2020. Objects are immutable blobs; "rename" is copy plus delete. Give browsers **presigned URLs** so uploads go straight to S3 instead of through your JVM.
- **SQS Standard** is at-least-once and best-effort ordered, so consumers must be **idempotent**. **FIFO** queues give ordering per *message group* and deduplication within a 5-minute window, at lower throughput. Always configure a **dead-letter queue** and set the visibility timeout longer than your processing time.
- **DynamoDB** is designed from **access patterns first**: you choose partition and sort keys for the queries you will run. A hot partition key (for example `status=PENDING`) throttles even when total capacity is fine. Transactions exist but are limited; scans are expensive.
- **Aurora** separates compute from a replicated storage layer (six copies across three AZs), fails over faster than classic RDS and supports up to 15 read replicas. It is still a single-writer relational database at heart.
- **Lambda with Java** suffers cold starts (JVM plus Spring context). Use **SnapStart**, keep the function small, or choose containers for latency-sensitive APIs. Lambda scaling to hundreds of concurrent executions can exhaust database connections; **RDS Proxy** pools them.
- **ElastiCache** is a cache, not a database of record. Plan for node failure (replica promotion, cold cache, thundering herd on the database).
- **Multi-AZ** protects against a data-centre failure inside one region. **Multi-region** is a separate, much more expensive decision (see `/system-design/senior/multi-region-disaster-recovery`).

## How to answer "which service would you use?"

1. Restate the workload: request/response or async? steady or spiky? data shape and consistency needs?
2. Name the default managed option and **one reason**.
3. Name the **limit or cost** that would make you switch.
4. Mention the operational concern: monitoring, failure mode, who gets paged.

Example: "For the PDF-generation job I'd put requests on SQS and run a worker on Fargate rather than Lambda, because some reports take 20 minutes and Lambda caps at 15. If volume were small and jobs short, Lambda would be cheaper and simpler."

## Cost is a design input

Seniors are expected to know where money silently goes: **NAT Gateway data processing**, cross-AZ traffic, over-provisioned RDS instances, CloudWatch log retention set to "never expire", idle load balancers, and Lambda functions with oversized memory. Mention cost alongside latency and availability and you sound like someone who has run production.
"""))

NOTES.append(("cloud-iam-vpc", "IAM and VPC Basics: Identity, Least Privilege and Network Boundaries", r"""
Two AWS topics come up in almost every backend interview that touches cloud: **who is allowed to do what (IAM)** and **who can reach what over the network (VPC)**. Get the mental model right and most follow-up questions answer themselves.

## IAM in five ideas

1. **Principals** make requests: IAM users (humans, ideally via SSO instead), **roles** (assumed by services, pods, CI pipelines, other accounts) and AWS services themselves.
2. **Policies** are JSON documents that allow or deny actions on resources, optionally with conditions.
3. **Default deny.** Nothing is allowed unless a policy allows it; an explicit `Deny` always wins.
4. **Roles over keys.** Workloads get temporary credentials by assuming a role: EC2 instance profiles, ECS task roles, EKS Pod Identity or IRSA, GitHub Actions OIDC federation. Long-lived access keys in `application.yml` or environment variables are a red flag.
5. **Least privilege.** Grant the specific actions on the specific resources the service needs.

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:GetObject", "s3:PutObject"],
    "Resource": "arn:aws:s3:::invoices-prod/tenant-uploads/*"
  }, {
    "Effect": "Allow",
    "Action": ["sqs:SendMessage"],
    "Resource": "arn:aws:sqs:ap-south-1:123456789012:invoice-generated"
  }]
}
```

Compare that with `"Action": "s3:*", "Resource": "*"`, which lets a compromised service read every bucket in the account. The AWS SDK for Java picks up role credentials automatically through its default credential provider chain, so the code needs no secrets at all.

**Interview nuance:** *identity-based* policies attach to a role; *resource-based* policies attach to the resource (an S3 bucket policy, an SQS queue policy) and are how you grant cross-account access. **Permission boundaries** and **SCPs** (organisation-level guardrails) cap what any policy can grant.

## VPC: your private network in a region

```text
VPC 10.0.0.0/16 (ap-south-1)
+-------------------------------------------------------------+
|  AZ-a                               AZ-b                    |
|  Public subnet 10.0.1.0/24          Public 10.0.2.0/24      |
|   [ALB node] [NAT GW]                [ALB node] [NAT GW]    |
|        |                                   |                |
|  Private subnet 10.0.11.0/24        Private 10.0.12.0/24    |
|   [ECS tasks / EKS pods]             [ECS tasks / EKS pods] |
|        |                                   |                |
|  Isolated subnet 10.0.21.0/24       Isolated 10.0.22.0/24   |
|   [Aurora writer]                    [Aurora reader]        |
+-------------------------------------------------------------+
  Internet Gateway attached to VPC; S3 gateway endpoint in route tables
```

- A **public subnet** has a route to an **Internet Gateway**. Only things that must be reachable from the internet live here, mainly load balancers and NAT gateways.
- A **private subnet** has no inbound route from the internet. Outbound calls (to a payment gateway or a public API) go through a **NAT Gateway** in a public subnet.
- An **isolated** subnet has no internet route at all, which suits databases.
- Spread every tier across **at least two Availability Zones**.

## Security groups vs network ACLs

| | Security group | Network ACL |
|---|---|---|
| Attached to | ENI (instance, task, RDS) | Subnet |
| State | **Stateful** (return traffic allowed automatically) | Stateless (allow both directions) |
| Rules | Allow only | Allow and deny, ordered |
| Typical use | Main control: "DB accepts 3306 only from the app's SG" | Coarse subnet-level blocks |

The senior pattern is to **reference security groups instead of IP ranges**: the RDS security group allows port 3306 from `sg-app`, so any new task in that group can connect while nothing else can, no matter how IPs change.

## VPC endpoints save money and reduce exposure

Without endpoints, traffic from private subnets to S3, DynamoDB, SQS or Secrets Manager goes through the NAT Gateway, which charges per GB processed. A **gateway endpoint** (S3, DynamoDB) is free, and **interface endpoints** (PrivateLink) keep traffic to other AWS APIs off the internet. A classic cost win: a batch job copying terabytes to S3 through NAT, fixed with one gateway endpoint.

## Questions to expect

- "Your service in a private subnet can't call Razorpay's API. What do you check?" Route table has `0.0.0.0/0` to a NAT in a public subnet, the security group allows outbound 443, the NACL allows ephemeral return ports, and DNS resolution works.
- "How does the app get its DB password?" From Secrets Manager or SSM Parameter Store, fetched with the task role; never baked into the image.
- "A developer laptop needs to query prod RDS." Use SSM Session Manager or a bastion with short-lived access and an audit trail, not a public database endpoint.
"""))

NOTES.append(("cloud-docker-spring", "Docker for Spring Boot: Images, Layers and Multi-stage Builds", r"""
A Docker **image** is a stack of read-only layers plus metadata (entrypoint, env, exposed ports). A **container** is a running process using that image with a thin writable layer on top, isolated with Linux namespaces and constrained by cgroups. It is not a VM: there is one shared kernel.

## Why layers matter

Each Dockerfile instruction that changes the filesystem creates a layer. Layers are cached and reused **only if every earlier layer is unchanged**. So put things that rarely change first and things that change every commit last.

A naive Spring Boot image:

```dockerfile
FROM eclipse-temurin:21-jdk
COPY target/app.jar /app.jar
ENTRYPOINT ["java","-jar","/app.jar"]
```

Problems: a full JDK in production (big, more CVEs), the whole 80 MB fat jar is one layer that changes on every commit, it runs as root, and the build happens outside Docker so it isn't reproducible.

## A production-grade multi-stage build

```dockerfile
# ---- build stage: has Maven and the JDK, never shipped ----
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /src
COPY pom.xml .
RUN mvn -q dependency:go-offline          # cached until pom.xml changes
COPY src ./src
RUN mvn -q package -DskipTests

# ---- extract Spring Boot layers ----
FROM eclipse-temurin:21-jre AS extract
WORKDIR /x
COPY --from=build /src/target/*.jar app.jar
RUN java -Djarmode=tools -jar app.jar extract --layers --destination out

# ---- runtime stage: JRE only, non-root ----
FROM eclipse-temurin:21-jre
RUN useradd --system --uid 10001 spring
WORKDIR /app
COPY --from=extract /x/out/dependencies/ ./
COPY --from=extract /x/out/spring-boot-loader/ ./
COPY --from=extract /x/out/snapshot-dependencies/ ./
COPY --from=extract /x/out/application/ ./
USER 10001
EXPOSE 8080
ENTRYPOINT ["java","-XX:MaxRAMPercentage=75","-jar","app.jar"]
```

What this buys you:

- **Small runtime image**: no Maven, no JDK, no source code.
- **Layer caching**: `dependencies/` (tens of MB) is reused across builds and pulls; a code change ships only the small `application/` layer.
- **Non-root user**: a container breakout or RCE starts with fewer privileges.
- **Exec-form ENTRYPOINT** (JSON array): Java runs as PID 1 and receives `SIGTERM` directly, so Spring's graceful shutdown works. The shell form (`ENTRYPOINT java -jar ...`) wraps it in `/bin/sh`, which may not forward signals.

The `-Djarmode=tools ... extract --layers` command is the Spring Boot 3.3+ way; older guides use `-Djarmode=layertools`. Spring Boot can also build an OCI image with no Dockerfile at all via Cloud Native Buildpacks (`mvn spring-boot:build-image`), which is a good answer when the team doesn't want to maintain Dockerfiles. On Java 25 the Spring docs also suggest a training run to create an AOT cache for faster startup.

## JVM inside containers

Modern JVMs (Java 10+, backported to 8u191) read cgroup limits. By default the max heap is **25% of the container memory limit**, often too small. Prefer `-XX:MaxRAMPercentage=70..75` over a hard-coded `-Xmx`, so heap scales with the limit while leaving room for metaspace, thread stacks, direct buffers and the code cache. If heap plus non-heap exceeds the limit, the kernel kills the container (**OOMKilled**, exit code 137) without any Java `OutOfMemoryError`.

## Best-practice checklist

- Pin base images to a version (`21-jre`), ideally to a **digest** in regulated setups; rebuild regularly to pick up OS patches.
- Use a `.dockerignore` (`target/`, `.git/`, `node_modules/`, `.env`) so secrets and junk never enter the build context.
- **Never put secrets in the image**: no `ENV DB_PASSWORD=...`, no copying `application-prod.yml` with passwords. Anyone who can pull the image can read every layer with `docker history` or by unpacking it.
- One process per container; log to **stdout/stderr**, not files.
- Scan images in CI (Trivy, Grype, ECR scanning) and fail the build on critical CVEs with a known fix.
- Combine `apt-get update && apt-get install ... && rm -rf /var/lib/apt/lists/*` into one `RUN`, or better, avoid package installs in the runtime image.
- Consider distroless or minimal JRE images when you don't need a shell; keep a debug variant or use `kubectl debug` for troubleshooting.
- Tag images with the **git SHA**, not just `latest`, so every deployment is traceable and rollbacks are exact.

## Interview angle

When asked to "review this Dockerfile", rank findings by risk: secrets in layers and running as root first, then missing JVM memory settings, then image size and caching. That is the same "correctness and security before style" ordering interviewers want in code review rounds.
"""))

NOTES.append(("cloud-k8s-core", "Kubernetes Essentials: Pods, Deployments, Services, Ingress, Config", r"""
Kubernetes is a **declarative control loop**: you submit desired state (YAML) to the API server, and controllers keep reconciling actual state towards it. If a pod dies, the ReplicaSet controller notices fewer replicas than desired and creates another. That one idea explains most behaviour.

## The objects you must know

```text
            Ingress / Gateway (HTTP routing, TLS)
                     |
                Service (stable virtual IP + DNS name)
                     |  selects pods by label app=orders
     Deployment --> ReplicaSet --> Pod  Pod  Pod
                                  (1+ containers, shared network/IP)
     ConfigMap / Secret --> mounted as env vars or files
```

- **Pod**: smallest unit; one or more containers sharing an IP and volumes. Pods are disposable and get new IPs when recreated, so never address them directly.
- **Deployment**: manages ReplicaSets for stateless apps and handles rolling updates and rollbacks.
- **StatefulSet**: stable names and per-pod volumes (databases, Kafka). Most backend services are Deployments.
- **Service**: stable endpoint that load-balances across matching pods. Types: `ClusterIP` (internal, default), `NodePort`, `LoadBalancer` (cloud LB per service).
- **Ingress / Gateway API**: L7 routing (host/path to service, TLS). The community **ingress-nginx** controller was retired in March 2026, and Kubernetes now points to **Gateway API** as the modern replacement, so mention it if asked about Ingress in 2026.
- **ConfigMap / Secret**: configuration injected as env vars or mounted files.
- **Namespace**: logical grouping for teams/environments with quotas and RBAC.

## A minimal but realistic Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders
spec:
  replicas: 3
  selector:
    matchLabels: { app: orders }
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1          # at most 1 extra pod during rollout
      maxUnavailable: 0    # never drop below 3 ready pods
  template:
    metadata:
      labels: { app: orders }
    spec:
      terminationGracePeriodSeconds: 40
      containers:
        - name: app
          image: 1234.dkr.ecr.ap-south-1.amazonaws.com/orders:3f9c2ab
          ports: [{ containerPort: 8080 }]
          envFrom:
            - configMapRef: { name: orders-config }
            - secretRef: { name: orders-db }
          resources:
            requests: { cpu: "500m", memory: "768Mi" }
            limits:   { memory: "768Mi" }
          readinessProbe:
            httpGet: { path: /actuator/health/readiness, port: 8080 }
            periodSeconds: 5
          livenessProbe:
            httpGet: { path: /actuator/health/liveness, port: 8080 }
            periodSeconds: 10
            failureThreshold: 3
          startupProbe:
            httpGet: { path: /actuator/health/liveness, port: 8080 }
            periodSeconds: 5
            failureThreshold: 30   # up to 150 s to start
---
apiVersion: v1
kind: Service
metadata:
  name: orders
spec:
  selector: { app: orders }
  ports: [{ port: 80, targetPort: 8080 }]
```

Other services call it at `http://orders.<namespace>.svc.cluster.local` (or just `http://orders` within the namespace) via cluster DNS.

## Rolling updates, step by step

Changing the image tag creates a new ReplicaSet. With `maxSurge: 1, maxUnavailable: 0`, Kubernetes starts one new pod, waits until its **readiness probe** passes, then terminates one old pod, and repeats. If new pods never become ready, the rollout stalls instead of taking the service down, and `kubectl rollout undo deployment/orders` returns to the previous ReplicaSet. This only works if readiness is meaningful and the new version is **backward compatible** with the old one (same DB schema, same message formats), because both run at the same time.

## Config and secrets

- Keep environment-specific values in ConfigMaps; Spring Boot maps env vars like `SPRING_DATASOURCE_URL` to properties automatically.
- **Kubernetes Secrets are base64-encoded, not encrypted** by default. Protect them with etcd encryption at rest, tight RBAC (who can `get secrets`), and ideally an external store such as AWS Secrets Manager or Vault synced via the External Secrets Operator or the Secrets Store CSI driver.
- Env vars are read once at startup; changing a ConfigMap does not restart pods. Trigger a rollout (for example, a checksum annotation in the pod template) or use mounted files with reload support.

## Commands worth having in muscle memory

```bash
kubectl get pods -o wide                     # status, restarts, node
kubectl describe pod orders-7d9f-abcde       # events: scheduling, probe failures, OOMKilled
kubectl logs orders-7d9f-abcde --previous    # logs of the crashed container
kubectl rollout status deployment/orders
kubectl rollout undo deployment/orders
kubectl top pods                             # needs metrics-server
kubectl exec -it orders-7d9f-abcde -- sh     # if the image has a shell
```

Interviewers rarely want YAML from memory; they want you to explain **why** each field exists and what breaks when it's missing.
"""))

NOTES.append(("cloud-k8s-production", "Kubernetes in Production: Probes, Resources, HPA and Why Pods Die", r"""
Getting a pod to run is easy. Keeping a Spring Boot service healthy under real traffic is what senior interviews probe. Four areas cover most questions: **probes, resources, autoscaling and failure states**.

## Probes: three different questions

| Probe | Question it answers | On failure | Spring Boot endpoint |
|---|---|---|---|
| **Startup** | Has the app finished starting? | Keeps restarting only after the threshold; other probes wait | `/actuator/health/liveness` with a generous threshold |
| **Readiness** | Should this pod receive traffic right now? | Removed from Service endpoints, **not restarted** | `/actuator/health/readiness` |
| **Liveness** | Is the process stuck beyond repair? | Container **restarted** | `/actuator/health/liveness` |

Spring Boot enables these health groups automatically when it detects Kubernetes (set `management.endpoint.health.probes.enabled=true` to get them elsewhere). The classic mistake is putting the **database check in liveness**: the DB has a 30-second blip, every pod fails liveness, Kubernetes restarts all of them at once, and a minor incident becomes a full outage with cold JVMs stampeding the recovering database. Dependencies belong in **readiness** at most, and often not even there, since you may prefer to serve degraded responses.

## Requests, limits and QoS

- **requests** are what the scheduler reserves; a pod is placed only on a node with that much unreserved capacity.
- **limits** are enforced at runtime. CPU over the limit is **throttled** (latency spikes, slow GC). Memory over the limit is **killed** (OOMKilled, exit code 137).
- QoS class: requests equal to limits gives **Guaranteed** (evicted last); some requests gives **Burstable**; none gives **BestEffort** (evicted first under node pressure).

A common, defensible setup for JVM services: set memory request **equal to** memory limit (predictable, no overcommit surprises), set a CPU request, and either skip the CPU limit or set it generously, because throttling a JVM during startup or GC hurts badly. Be ready to defend whichever choice you make.

## Why pods get OOMKilled

```text
container limit 1 GiB
 |-- heap (MaxRAMPercentage=75)      768 MiB
 |-- metaspace + code cache           ~150 MiB
 |-- thread stacks (200 x 1 MiB)      ~200 MiB   <-- already over!
 |-- direct buffers (Netty, NIO)        ?
```

The kernel counts the **whole process**, not just heap. Fixes: lower `MaxRAMPercentage`, cap threads (Tomcat `server.tomcat.threads.max`, or virtual threads), cap direct memory, raise the limit, and look for real leaks with heap dumps. If the JVM throws `OutOfMemoryError: Java heap space` instead, the heap itself is too small or leaking, which is a different problem.

## CrashLoopBackOff: a debugging routine

CrashLoopBackOff means "the container keeps exiting, and Kubernetes waits longer between restarts (up to 5 minutes)". It is a symptom, not a cause.

1. `kubectl describe pod` shows the last state, **exit code** and events. 137 means killed (OOM, or a liveness failure); 1 means the app exited with an error; 143 means SIGTERM.
2. `kubectl logs <pod> --previous` shows the crashed container's output, typically a Spring startup failure: missing env var, bad datasource URL, failed Flyway migration, a secret that doesn't exist.
3. Check probes: a liveness probe that starts before the app is up kills it forever. Add a **startup probe**.
4. Check config drift: what changed? image tag, ConfigMap, Secret, node pool.
5. Mitigate first (`kubectl rollout undo`), then root-cause.

Other states to recognise: **Pending** (no node with enough requested CPU/memory, or an unbound volume), **ImagePullBackOff** (wrong tag, missing registry credentials), **Evicted** (node under memory or disk pressure).

## Horizontal Pod Autoscaler

HPA periodically computes:

```text
desiredReplicas = ceil(currentReplicas * currentMetric / targetMetric)
e.g. 4 pods at 90% CPU, target 60%  ->  ceil(4 * 90 / 60) = 6 pods
```

Utilisation is measured **against requests**, so wrong requests mean wrong scaling. CPU is a poor signal for I/O-bound services waiting on a database; scale on request rate, queue depth (KEDA for SQS/Kafka lag) or latency instead. Also remember HPA cannot help when the bottleneck is downstream: adding pods to a service blocked on a saturated MySQL just adds more connections and makes it worse.

## Graceful shutdown and disruptions

When a pod is terminated, Kubernetes sends SIGTERM and, in parallel, removes it from endpoints. To avoid dropped requests:

- `server.shutdown=graceful` and `spring.lifecycle.timeout-per-shutdown-phase=30s` let in-flight requests finish.
- A short `preStop` sleep (5-10 s) gives load balancers time to stop sending new traffic.
- `terminationGracePeriodSeconds` must exceed preStop plus shutdown time.
- A **PodDisruptionBudget** (`minAvailable: 2`) stops node drains during cluster upgrades from evicting too many replicas at once.
- Spread replicas across zones with topology spread constraints so one AZ failure doesn't take all pods.

Tie it together in interviews: "readiness controls traffic, liveness controls restarts, requests control placement and autoscaling, limits control kills."
"""))

NOTES.append(("cloud-cicd-releases", "CI/CD, Deployment Strategies, Feature Flags and Rollbacks", r"""
At a product company you ship many times a week, so the **pipeline and release strategy are part of the design**. Interviewers want to hear how you keep deploys boring.

## A pipeline that works for a Spring Boot service

```text
PR opened ---> CI: compile, unit tests, static analysis, dependency + secret scan
merge to main
   ---> build image ONCE (tag = git SHA), scan, push to registry, SBOM
   ---> deploy to dev  -> integration / contract tests (Testcontainers, Pact)
   ---> deploy to staging -> smoke + light load test
   ---> prod: canary 5% -> watch SLOs -> 25% -> 100%   (auto-rollback on alarms)
```

Principles worth saying out loud:

- **Build once, promote the same artifact.** Never rebuild for prod; promote the image digest that passed staging. Config differs per environment, the binary doesn't.
- **Fast feedback**: PR checks under ~10 minutes, or people stop waiting for them.
- **Trunk-based development** with short-lived branches plus feature flags beats long release branches.
- **Pipeline as code** in the repo, reviewed like any code.
- **No humans with prod credentials** in the normal path: CI deploys with a role obtained through OIDC federation, not stored cloud keys.

```yaml
# .github/workflows/ci.yml (trimmed)
name: ci
on: [pull_request, push]
jobs:
  build:
    runs-on: ubuntu-latest
    permissions: { contents: read, id-token: write }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { distribution: temurin, java-version: '21', cache: maven }
      - run: mvn -B verify            # unit + Testcontainers integration tests
      - run: docker build -t $REGISTRY/orders:${{ github.sha }} .
      - run: trivy image --exit-code 1 --severity CRITICAL $REGISTRY/orders:${{ github.sha }}
```

## Deployment strategies

| Strategy | How | Good for | Watch out for |
|---|---|---|---|
| **Rolling** | Replace pods a few at a time | Default for stateless services | Old and new versions run together |
| **Blue-green** | Stand up full new stack, switch traffic at once | Fast, clean rollback (switch back) | Double capacity during the switch; DB is shared |
| **Canary** | Send a small % of traffic to the new version, compare metrics, increase | Catching problems with limited blast radius | Needs good metrics and enough traffic to compare |
| **Shadow / dark launch** | Mirror traffic to new version, discard responses | Risky rewrites | Side effects (don't double-charge!) |

A canary is only as good as its **analysis**: compare error rate, p99 latency and a business metric (orders per minute, payment success rate) between canary and baseline. Tools like Argo Rollouts or Flagger automate promotion and rollback against Prometheus queries.

## Feature flags: decouple deploy from release

Deploying puts code in production; **releasing** exposes behaviour to users. Flags let you merge unfinished work behind `false`, roll out to internal users, then 1%, 10%, 100%, and turn a feature off in seconds without a deploy.

Types: **release toggles** (short-lived), **ops toggles / kill switches** (turn off an expensive feature during an incident), **experiment toggles** (A/B tests), **permission toggles** (premium features).

Pitfalls interviewers like: flags never removed (dead code paths and combinatorial testing), flag evaluation calling a remote service on every request (cache it, have safe defaults when the flag service is down), and flags guarding schema changes that aren't actually reversible.

## Rollback vs roll forward

- **Roll back** when the cause is unclear or impact is high: it is the fastest proven-safe state. Make it one command or one click, and practise it.
- **Roll forward** (ship a fix) when the fix is tiny and well understood, or when rollback is unsafe.
- **Rollback is unsafe when data changed shape.** If v2 dropped a column or started writing a new enum value v1 can't read, going back breaks v1.

## Database changes without downtime: expand and contract

```text
1. Expand:   add new nullable column `phone_e164`        (old code ignores it)
2. Deploy:   code writes both columns, reads old          (rollback-safe)
3. Backfill: batch-migrate existing rows (throttled)
4. Switch:   code reads new column, still writes both     (rollback-safe)
5. Contract: stop writing old column, later drop it       (only after confidence)
```

Each step is backward compatible with the previous code version, so any single deploy can be rolled back. Tools: Flyway or Liquibase migrations in the pipeline; for big MySQL tables, online schema change tools (gh-ost, pt-online-schema-change) or MySQL 8 instant DDL where supported.

## Measuring delivery: DORA metrics

**Deployment frequency, lead time for changes, change failure rate, time to restore service** (DORA has also added a rework-rate measure in recent reports). Quoting these when describing your pipeline shows you think about delivery as a system, not a script.
"""))

NOTES.append(("cloud-12factor-iac", "12-Factor Apps and Infrastructure as Code with Terraform", r"""
## The twelve factors, translated for Spring Boot

The 12-factor methodology (Heroku, 2011) is still the cleanest checklist for "is this service cloud-ready?". You don't need all twelve memorised; know what each means in practice.

| Factor | In a Spring Boot service |
|---|---|
| 1. One codebase, many deploys | One repo per service; the same artifact goes to dev/staging/prod |
| 2. Explicit dependencies | `pom.xml` with pinned versions; no "it works because the server has library X" |
| 3. Config in the environment | Env vars, ConfigMaps, Secrets Manager; profiles for structure, not for prod passwords in git |
| 4. Backing services as attached resources | MySQL, Redis, SQS addressed by URL/credentials; swap without code change |
| 5. Build, release, run separated | CI builds an image; release = image + config; run = pods |
| 6. Stateless processes | No HTTP session in memory, no files on local disk; use Redis/S3 |
| 7. Port binding | Embedded Tomcat/Netty exposes 8080; no external app server |
| 8. Concurrency via processes | Scale out with more replicas (HPA), not bigger singletons |
| 9. Disposability | Fast startup, graceful shutdown on SIGTERM, idempotent jobs |
| 10. Dev/prod parity | Testcontainers with the real MySQL version, not H2 pretending to be MySQL |
| 11. Logs as event streams | JSON to stdout; the platform ships them (Fluent Bit, CloudWatch) |
| 12. Admin processes as one-off tasks | Migrations and backfills as Jobs using the same image |

The factors that cause the most production pain when violated are **3 (config)**, **6 (statelessness)** and **9 (disposability)**. Example: a scheduler running inside every replica with `@Scheduled` fires N times after scaling to N pods. Fix it with a distributed lock (ShedLock), a leader, or by moving the job to a Kubernetes CronJob or a queue.

Modern additions people mention: observability (metrics and traces, not just logs), security (identity per workload) and API-first contracts.

## Infrastructure as code: why

Clicking in the AWS console produces infrastructure nobody can review, reproduce or roll back. **IaC** puts infrastructure in version control: changes go through pull requests, environments are consistent, and disaster recovery means re-applying code.

Options: **Terraform/OpenTofu** (multi-cloud, huge ecosystem; OpenTofu is the open-source fork created after HashiCorp's 2023 licence change), **AWS CloudFormation / CDK** (AWS-native; CDK lets you write it in Java or TypeScript), **Pulumi** (general-purpose languages), and **Ansible** for configuring machines rather than provisioning cloud resources.

## Terraform in one page

```hcl
terraform {
  required_providers { aws = { source = "hashicorp/aws", version = "~> 5.0" } }
  backend "s3" {
    bucket       = "acme-tf-state"
    key          = "orders/prod.tfstate"
    region       = "ap-south-1"
    use_lockfile = true      # S3-native state locking (Terraform 1.10+)
    encrypt      = true
  }
}

resource "aws_sqs_queue" "orders_dlq" {
  name = "orders-dlq"
}

resource "aws_sqs_queue" "orders" {
  name                       = "orders"
  visibility_timeout_seconds = 120
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.orders_dlq.arn
    maxReceiveCount     = 5
  })
}
```

Key concepts:

- **Providers** talk to APIs (AWS, Kubernetes, Datadog). **Resources** are things Terraform manages; **data sources** read things it doesn't.
- **State** maps your code to real resource IDs. It must be **remote** (S3, Terraform Cloud) and **locked**, otherwise two engineers applying at once corrupt it. Older setups used a DynamoDB table for locking; newer Terraform versions support S3-native lock files. State can contain secrets, so encrypt it and restrict access.
- **`terraform plan`** shows the diff between code and reality; **`apply`** executes it. In CI: plan on PR (posted as a comment for review), apply on merge.
- **Modules** package reusable patterns ("a service with ALB target group, task definition, alarms").
- **Drift** is when someone changes infrastructure by hand. A scheduled `plan` that should show no changes detects it.
- **Dangerous diffs**: a plan that says "destroy and recreate" on a database. Use `prevent_destroy` lifecycle rules and read plans carefully, the same way you read a migration.

## GitOps for Kubernetes

Terraform typically provisions the cluster, networking and databases. Application manifests are often managed by **GitOps** tools (Argo CD, Flux): the desired Kubernetes state lives in a Git repo, and a controller in the cluster continuously syncs it. Deploying becomes "merge a PR that bumps the image tag"; rollback is "revert the commit", and every change has an audit trail.

## What to say in an interview

"Everything below the application is Terraform in a separate repo with remote state and locking; plans are reviewed in PRs. App manifests are Helm charts synced by Argo CD. Config comes from the environment and secrets from Secrets Manager, so the same image runs everywhere." That one paragraph answers half the follow-ups before they're asked.
"""))

# ---------------------------------------------------------------- Q&A
QA = []

QA.append(("Your team is launching a new Spring Boot REST service on AWS. How do you choose between ECS on Fargate, EKS, Lambda and plain EC2?", r"""
Start from the **workload and the team**, not the technology.

- **ECS on Fargate**: my default for a long-running HTTP API when the company isn't already on Kubernetes. No servers or cluster upgrades to manage, integrates with ALB, IAM task roles and CloudWatch. Downsides: AWS-specific, slightly higher per-vCPU cost than EC2.
- **EKS**: when the organisation already runs Kubernetes, needs portability, service mesh, or a large platform with many services. It brings real operational cost (upgrades every few months, add-ons, networking), so it needs platform engineers.
- **Lambda**: event-driven or spiky work (S3 uploads, queue consumers, cron jobs, low-traffic internal APIs). Limits: 15-minute max duration, Java cold starts (mitigate with SnapStart), and connection storms against RDS (use RDS Proxy).
- **EC2**: special hardware, licensed software, or very steady load where reserved/Graviton instances are cheapest, at the cost of patching and scaling yourself.

**Example answer:** "Orders API on Fargate behind an ALB, 3 tasks across 2 AZs, autoscaling on request count; the invoice PDF generator as an SQS consumer, also on Fargate because some jobs exceed 15 minutes. If we later had 30+ services and a platform team, I'd revisit EKS."
""", I, ["aws", "compute", "ecs", "lambda", "eks"], True))

QA.append(("When would you choose DynamoDB over RDS/Aurora MySQL for a new feature?", r"""
Choose **DynamoDB** when the access patterns are **known, simple and key-based**, and you need predictable single-digit-millisecond latency at very high or very spiky scale with no capacity or connection management. Good fits: user sessions, shopping carts, idempotency keys, device or IoT state, a feed keyed by `userId` and sorted by time.

Choose **RDS/Aurora** when you need **relational integrity and flexible queries**: joins, multi-row transactions across entities, ad-hoc reporting, evolving query needs. Orders, payments ledgers and inventory with constraints usually belong here.

Trade-offs to state:

| | DynamoDB | Aurora MySQL |
|---|---|---|
| Schema design | Access patterns first (PK/SK, GSIs) | Normalise, index later |
| New query type | May need a new GSI or a redesign | Add an index |
| Scaling | Horizontal, automatic | Vertical writer + read replicas |
| Pitfall | Hot partition keys, expensive scans | Connection limits, single writer |

**Senior nuance:** don't pick DynamoDB because it "scales" if you'll end up scanning tables for an admin dashboard. A common hybrid is Aurora as the system of record plus DynamoDB or ElastiCache for one hot, key-value access path.
""", I, ["aws", "dynamodb", "rds", "databases"], True))

QA.append(("An 'order placed' event must be consumed by inventory, notifications and analytics. Would you use SQS, SNS, EventBridge or Kafka (MSK)?", r"""
It depends on **fan-out, ordering, replay and throughput**.

- **SNS -> one SQS queue per consumer** (fan-out): simple, fully managed, each service gets its own queue, retries and DLQ, so a slow analytics consumer can't block inventory. At-least-once delivery, so consumers must be idempotent. My default for a handful of consumers at moderate volume.
- **EventBridge**: like SNS with content-based routing rules, schema registry and SaaS integrations. Good for many loosely coupled consumers and filtering ("only orders > Rs 10,000 to fraud check"). Higher latency and lower per-account throughput limits than SNS/SQS.
- **Kafka / MSK**: when you need **replay** (a new consumer reads last 7 days), strict **ordering per key** (all events of one order in sequence), very high throughput, or stream processing. Costs more to operate and needs partition and consumer-group design.
- **Plain SQS** alone is point-to-point: one message is processed by one consumer, so it doesn't fan out.

Whatever you pick, publish reliably: use the **transactional outbox** so the event is written in the same DB transaction as the order, then relayed, instead of "save order, then publish" which can lose events if the process crashes in between.
""", I, ["aws", "sqs", "sns", "kafka", "messaging"], True))

QA.append(("Users upload invoices and profile photos (up to 20 MB). How would you design uploads and downloads on AWS?", r"""
Don't stream large files through the Spring Boot JVM. Use **S3 presigned URLs**.

1. Client calls `POST /uploads` with file name, type and size. The service checks auth, validates type and size, and generates a key such as `tenant/123/invoices/<uuid>.pdf` (never the user's filename as the key).
2. Service returns a **presigned PUT URL** valid for about 5 minutes, scoped to exactly that key and content type.
3. Client uploads directly to S3.
4. An **S3 event** (to SQS or Lambda) triggers post-processing: virus scan, thumbnailing, extracting metadata, then marks the record `READY` in the DB.
5. Downloads: authorise in the service, then return a short-lived **presigned GET URL**, or serve public assets through **CloudFront** with origin access control so the bucket stays private.

Also mention: **Block Public Access** on the bucket, server-side encryption (SSE-S3 or SSE-KMS), lifecycle rules to move old invoices to cheaper storage classes, versioning for accidental deletes, and a size limit enforced in the presigned policy or post-upload check.

Benefits: app servers stay small, uploads scale independently, and S3 handles durability.
""", I, ["aws", "s3", "cloudfront", "design"], False))

QA.append(("Your Spring Boot service on ECS/EC2 needs to read from S3 and Secrets Manager. How should it get AWS credentials?", r"""
Through an **IAM role**, never through access keys in config.

- **ECS**: attach a **task role**; the container receives temporary credentials from the task metadata endpoint.
- **EC2**: use an **instance profile**.
- **EKS**: **EKS Pod Identity** or **IRSA** (IAM Roles for Service Accounts) maps a Kubernetes service account to an IAM role per workload.
- **CI/CD (GitHub Actions)**: OIDC federation to assume a deploy role, no stored secrets.

The AWS SDK for Java's default credential provider chain finds these automatically, so the code just builds `S3Client.create()`. Credentials are short-lived and rotate on their own.

Scope the role with **least privilege**: `s3:GetObject` on `arn:aws:s3:::invoices-prod/*` and `secretsmanager:GetSecretValue` on the one secret ARN, not `s3:*` on `*`.

**Why not access keys?** They are long-lived, end up in git, images, logs and laptops, and a leak gives an attacker access until someone notices and rotates them. If an interviewer asks "what if a key is leaked?", say: deactivate it immediately, check CloudTrail for what it was used for, rotate, and remove the root cause (move to roles).
""", B, ["aws", "iam", "security"], True))

QA.append(("Explain public vs private subnets. How does a service in a private subnet call an external payment API?", r"""
A **public subnet** has a route table entry `0.0.0.0/0 -> Internet Gateway`, so resources with public IPs can be reached from and reach the internet. Put only internet-facing components there: load balancers, NAT gateways, maybe a bastion.

A **private subnet** has no route from the internet. App servers and pods live here, so nobody can connect to them directly; traffic arrives only via the load balancer.

For **outbound** calls (Razorpay, Stripe, an SMS provider), the private subnet's route table sends `0.0.0.0/0` to a **NAT Gateway** sitting in a public subnet. The NAT translates the private source IP to its own Elastic IP, so responses come back, but no one can initiate a connection inward. A nice side effect: the partner can **allowlist your NAT's static IP**.

Databases often sit in **isolated** subnets with no internet route at all.

Senior details: deploy one NAT per AZ to avoid a cross-AZ single point of failure; NAT charges per GB, so use **VPC gateway endpoints** for S3/DynamoDB traffic; and for debugging connectivity check route tables, security group egress, NACL ephemeral ports and DNS.
""", B, ["aws", "vpc", "networking"], False))

QA.append(("What is the difference between a security group and a network ACL? How would you lock down an RDS database?", r"""
**Security groups** attach to network interfaces (EC2, ECS tasks, RDS). They are **stateful** (if inbound is allowed, the response is allowed automatically) and contain **allow rules only**. **Network ACLs** attach to subnets, are **stateless** (you must allow return traffic on ephemeral ports), support allow and deny, and are evaluated in rule-number order.

In practice, security groups are the main control and NACLs are a coarse extra layer (for example, blocking a known bad CIDR).

Locking down RDS:

1. Put it in **private/isolated subnets** with "publicly accessible" disabled.
2. Its security group allows **port 3306 only from the app's security group** (`sg-orders-app`), not from a CIDR like `10.0.0.0/16`. Referencing groups keeps working as task IPs change and excludes everything else in the VPC.
3. Require **TLS** connections and enable encryption at rest (KMS).
4. Store credentials in **Secrets Manager** with rotation, or use IAM database authentication.
5. Human access via SSM Session Manager or a bastion with audit logging, never by opening 3306 to an office IP.
""", B, ["aws", "vpc", "security", "rds"], False))

QA.append(("A Java Lambda behind API Gateway has 5-6 second cold starts and the p99 SLO is 1 second. What are your options?", r"""
First confirm it is cold starts (look at `Init Duration` in CloudWatch logs or X-Ray), and how often they happen. Then, from cheapest to most drastic:

1. **SnapStart** (Java 11+ managed runtimes): Lambda snapshots the initialised execution environment and restores it, cutting init time dramatically. Watch out for state that must be unique per environment (random seeds, open connections); use runtime hooks to refresh them.
2. **Slim the init path**: avoid full Spring Boot component scanning; use Spring Cloud Function with a minimal context, lazy initialisation, fewer dependencies, or a lighter framework. Initialise SDK clients once, outside the handler.
3. **More memory**: CPU scales with memory, so init and JIT run faster; often cost-neutral because duration drops.
4. **Provisioned concurrency** for predictable traffic: pre-warmed environments, paid for whether used or not.
5. **GraalVM native image**: millisecond starts, but longer builds and reflection configuration.
6. **Change the compute model**: if traffic is steady and latency-critical, a container on Fargate with a warm JVM is simpler and cheaper.

A senior answer ends with the trade-off: "SnapStart first; if we're paying for provisioned concurrency around the clock, we've basically rebuilt a container service and should move to one."
""", I, ["aws", "lambda", "performance"], False))

QA.append(("After scaling your service from 6 to 40 pods (or moving to Lambda), MySQL starts returning 'Too many connections'. Why, and how do you fix it?", r"""
Each pod has its own **HikariCP pool**. 40 pods x `maximumPoolSize=20` = up to **800 connections**, past the RDS instance's `max_connections` (which scales with instance memory). Lambda is worse: every concurrent execution may open its own connection, so a spike of 500 invocations means 500 connections.

**Fixes:**

- **Right-size pools**: most services need far fewer connections than threads. Start with roughly `cores * 2` per pod and measure pool wait time (`hikaricp.connections.pending`). A total budget per database, divided across replicas, is a good conversation to have.
- **Cap autoscaling** so `maxReplicas x poolSize` stays under the DB limit, or scale on a metric that reflects DB capacity.
- **Connection proxy**: **RDS Proxy** (essential for Lambda) or ProxySQL multiplexes many client connections onto fewer DB connections.
- **Reduce DB load per request**: caching, fixing N+1 queries, moving reads to replicas.
- **Bigger instance** raises `max_connections`, but that's a cost lever, not a design fix.

The key insight: horizontal scaling of stateless services shifts the bottleneck to the shared stateful dependency. Scaling the app tier without thinking about the database is a classic mid-level mistake.
""", I, ["aws", "rds", "mysql", "scaling", "hikaricp"], False))

QA.append(("Your Spring Boot Docker image is 700 MB and every build re-uploads everything, taking 5 minutes. How do you fix it?", r"""
Diagnose with `docker history <image>` to see which layers are big and which change.

Typical causes and fixes:

1. **JDK and build tools in the runtime image** -> use a **multi-stage build**: Maven + JDK in the build stage, only a **JRE** (or distroless/minimal JRE) in the final stage.
2. **Fat jar as one layer** -> extract Spring Boot layers (`java -Djarmode=tools -jar app.jar extract --layers`) and `COPY` `dependencies/`, `spring-boot-loader/`, `snapshot-dependencies/`, `application/` separately. Dependencies rarely change, so a code change ships only a few hundred KB.
3. **Cache-busting order** -> `COPY pom.xml` and run `mvn dependency:go-offline` **before** `COPY src`, so dependency download is cached until the POM changes. Use BuildKit cache mounts (`RUN --mount=type=cache,target=/root/.m2`).
4. **Huge build context** -> add `.dockerignore` (`target/`, `.git/`, `node_modules/`).
5. **OS package installs** -> remove them or clean apt lists in the same `RUN`.

Results are usually a ~200-300 MB image where daily pushes and pulls move only the application layer. Alternative: Spring Boot **Buildpacks** (`mvn spring-boot:build-image`) produce well-layered images with no Dockerfile to maintain.
""", I, ["docker", "spring-boot", "ci"], True))

QA.append(("You're reviewing a teammate's Dockerfile. What's on your checklist, in priority order?", r"""
Rank by production risk, not style:

1. **Secrets**: no `ENV`/`ARG` passwords, no copied `.env` or prod config with credentials; they persist in layers even if deleted later. Use build secrets (`--mount=type=secret`) for private registries.
2. **Runs as non-root** (`USER 10001`), no unnecessary capabilities; read-only root filesystem where possible.
3. **Trusted, pinned base image** (`eclipse-temurin:21-jre`, or a digest), from an official source; rebuilt regularly for patches.
4. **Correct process handling**: exec-form `ENTRYPOINT ["java", ...]` so SIGTERM reaches the JVM and graceful shutdown works.
5. **JVM memory**: `-XX:MaxRAMPercentage` sized to the container limit, so the pod isn't OOMKilled.
6. **Minimal contents**: multi-stage, JRE only, no compilers, curl or package managers unless needed (smaller attack surface).
7. **Layer caching and size**: dependencies before source, Spring Boot layers, `.dockerignore`.
8. **Logs to stdout**, one process per container, health check handled by the orchestrator.
9. **Image scanning** in CI with a clear policy (fail on fixable critical CVEs).
10. **Traceable tags**: git SHA, not `latest`.

Saying "1 and 2 are blocking, 7 is a suggestion" shows the judgement interviewers look for in review rounds.
""", I, ["docker", "security", "code-review"], False))

QA.append(("Your Spring Boot pod keeps getting OOMKilled (exit code 137), but heap usage in your dashboards looks fine. What's going on?", r"""
OOMKilled means the **Linux kernel killed the container** for exceeding its cgroup **memory limit**. The kernel counts the whole process, not just the Java heap, so "heap looks fine" is consistent with it.

JVM memory = **heap + metaspace + code cache + thread stacks + direct/NIO buffers + GC structures + native libraries**. Common culprits:

- `-Xmx` set close to the limit (e.g. `-Xmx1g` with a 1 GiB limit), leaving nothing for non-heap.
- Hundreds of platform threads (Tomcat max threads, unbounded executors), roughly 1 MB of stack each.
- Netty/NIO direct buffers growing (WebClient, Kafka, Redis clients).
- A native memory leak (JNI library, unclosed compressors).

**Debugging:** `kubectl describe pod` (Last State: OOMKilled), compare `container_memory_working_set_bytes` with the limit, enable **Native Memory Tracking** (`-XX:NativeMemoryTracking=summary`, then `jcmd <pid> VM.native_memory summary`) to see each region.

**Fixes:** use `-XX:MaxRAMPercentage=70-75` instead of a hard `-Xmx`, cap thread pools (or use virtual threads for I/O-bound work), limit direct memory (`-XX:MaxDirectMemorySize`), set memory request = limit for predictability, and only then raise the limit. If you see `java.lang.OutOfMemoryError` in logs instead, that's a heap problem: take a heap dump.
""", A, ["kubernetes", "jvm", "oomkilled", "debugging"], True))

QA.append(("After a deploy, the new pods are in CrashLoopBackOff. Walk me through how you handle it.", r"""
**Mitigate first, then debug.** If the rollout is stuck with old pods still serving (thanks to `maxUnavailable: 0`), users may be fine; otherwise `kubectl rollout undo deployment/orders` immediately.

Then investigate:

1. `kubectl get pods` shows restart counts. `kubectl describe pod <pod>` gives **Last State, exit code and events**: `137` = killed (OOM or failed liveness), `1` = application error, `143` = SIGTERM.
2. `kubectl logs <pod> --previous` shows the crashed container's logs. Typical Spring Boot causes: missing env var or Secret key, wrong datasource URL, Flyway migration failure, bean creation exception after a dependency upgrade, port already in use.
3. **Probes**: if logs show the app starting normally and then getting killed, the liveness probe may fire before startup completes. Add a startup probe or raise its threshold.
4. **What changed?** Diff image tag, ConfigMap, Secret, resource limits, and the base image. `kubectl rollout history` helps.
5. Reproduce locally with the same image and env (`docker run` with the same variables).

After the fix: add a guardrail so it can't recur silently, for example config validation at startup (`@ConfigurationProperties` with `@Validated`), a smoke test in staging, or a canary that blocks promotion.
""", I, ["kubernetes", "debugging", "crashloopbackoff"], True))

QA.append(("What should liveness, readiness and startup probes check in a Spring Boot service? Why is checking the database in liveness dangerous?", r"""
- **Startup probe**: "has the JVM and Spring context finished starting?" Use a generous `failureThreshold x periodSeconds` (e.g. 30 x 5s). Liveness and readiness don't run until it passes, so slow starts aren't killed.
- **Readiness** (`/actuator/health/readiness`): "can this instance serve traffic now?" Failing removes the pod from the Service, without restarting it. Use it during warm-up, graceful shutdown, or when a critical local resource isn't ready.
- **Liveness** (`/actuator/health/liveness`): "is this process irrecoverably broken (deadlocked, stuck)?" Failing restarts the container. It should depend only on the app's **own** internal state.

**Why not the DB in liveness?** If MySQL has a 20-second failover, every pod fails liveness simultaneously, Kubernetes restarts all of them, and you get cold JVMs, empty caches and a reconnect storm hitting a database that is just recovering. A dependency blip turns into a full outage, and restarts can't fix a remote database anyway.

Even in readiness, think twice: if all pods go unready because a shared dependency is down, the Service has zero endpoints and users get connection errors instead of a friendly degraded response. Spring Boot's default probe groups intentionally exclude external checks.
""", I, ["kubernetes", "probes", "spring-boot", "actuator"], True))

QA.append(("Explain Kubernetes requests vs limits. Should you set CPU limits on a JVM service?", r"""
- **Requests** are reservations used by the **scheduler** (a pod only lands on a node with that much unreserved capacity) and by **HPA**, which measures utilisation as a percentage of requests.
- **Limits** are runtime caps. Exceeding **memory** gets the container OOMKilled; exceeding **CPU** gets it **throttled** by the CFS quota.

QoS follows from them: requests = limits for all resources is **Guaranteed**; partial is **Burstable**; none is **BestEffort**, which is evicted first under node pressure.

**CPU limits on JVMs** are genuinely debated:

- *Against*: the JVM is bursty (startup, JIT compilation, GC threads). A low limit throttles these bursts, producing latency spikes and slow startup even when the node has idle CPU. Many teams set a **CPU request but no CPU limit**, so pods can use spare capacity.
- *For*: multi-tenant clusters where one noisy service must not starve others, or when you need predictable cost and capacity.

A reasonable position: **memory request = memory limit** always; CPU request based on measured usage; CPU limit either absent or generous (2-4x request), and watch `container_cpu_cfs_throttled_periods_total`. Also note the JVM sizes GC and thread pools from the visible CPU count, so very small limits can mis-tune it.
""", A, ["kubernetes", "resources", "jvm"], False))

QA.append(("How does the Horizontal Pod Autoscaler work, and why might scaling on CPU not help your service?", r"""
HPA runs a control loop (every ~15 s) that reads metrics and computes:

`desired = ceil(current * currentValue / targetValue)`

For example, 4 pods at 90% CPU with a 60% target gives `ceil(4 * 90/60) = 6`. It respects `minReplicas`/`maxReplicas` and a scale-down stabilisation window (default 5 minutes) to avoid flapping. CPU utilisation is measured **relative to requests**, so wrong requests produce wrong decisions.

**Why CPU may not help:**

- **I/O-bound services** (most Spring Boot CRUD apps) spend time waiting on DB or HTTP calls; latency rises while CPU stays low, so HPA never scales.
- **Downstream bottleneck**: if MySQL is saturated, more pods mean more connections and more contention, making it worse.
- **Queue consumers**: backlog grows while each worker is idle-waiting; scale on **queue depth / consumer lag** instead (KEDA supports SQS, Kafka, RabbitMQ).
- **Slow startup**: a JVM taking 60 s to become ready reacts too late to a sudden spike; keep headroom with a higher `minReplicas` or scheduled scaling for known peaks.

Better signals: requests per second per pod, p95 latency, or queue lag via custom/external metrics.
""", I, ["kubernetes", "hpa", "autoscaling"], False))

QA.append(("How do you achieve zero-downtime deployments for a Spring Boot service on Kubernetes?", r"""
Several pieces must all be in place:

1. **Rolling update with `maxUnavailable: 0`, `maxSurge: 1`** so capacity never drops.
2. **Meaningful readiness probe**: new pods get traffic only after Spring is fully started and warmed.
3. **Graceful shutdown**: `server.shutdown=graceful` plus `spring.lifecycle.timeout-per-shutdown-phase` so in-flight requests finish after SIGTERM.
4. **preStop hook** (`sleep 10`): endpoint removal propagates to kube-proxy/ingress asynchronously; the sleep stops new requests arriving at a pod that is shutting down.
5. **`terminationGracePeriodSeconds`** greater than preStop + shutdown timeout.
6. **Backward compatibility**: old and new versions run side by side, so DB changes follow **expand/contract**, APIs stay backward compatible, and message consumers tolerate both old and new event formats.
7. **PodDisruptionBudget** and multiple replicas across zones, so node drains don't remove all capacity.
8. **Long-lived connections** (WebSockets, gRPC streams) need client reconnect logic.
9. **Verify with a canary or automated rollback** on error-rate alarms.

Interviewers often stop at the first two; mentioning preStop timing and schema compatibility is what signals real production experience.
""", I, ["kubernetes", "deployment", "spring-boot", "zero-downtime"], True))

QA.append(("ConfigMap vs Secret: are Kubernetes Secrets actually secure? How would you manage secrets for your services?", r"""
**ConfigMaps** hold non-sensitive config; **Secrets** hold credentials and are handled slightly more carefully (not shown in `describe`, can be mounted as tmpfs). But by default a Secret is only **base64-encoded**, which is an encoding, not encryption. Anyone with `get secrets` RBAC in the namespace, or access to etcd backups, can read it.

Hardening steps:

- **Encryption at rest** for etcd (managed clusters like EKS support KMS envelope encryption).
- **Tight RBAC**: developers can deploy but not read prod secrets; separate namespaces.
- **External source of truth**: AWS Secrets Manager / SSM Parameter Store / HashiCorp Vault, synced via **External Secrets Operator** or mounted via the **Secrets Store CSI driver**. This gives audit logs, rotation and one place to revoke.
- **Workload identity** (IRSA/Pod Identity) so the pod can fetch its own secret without a bootstrap credential.
- **Never commit secrets to git**, even in Helm values. If GitOps is required, use Sealed Secrets or SOPS-encrypted files.
- **Rotation**: prefer short-lived credentials (IAM DB auth, Vault dynamic DB credentials). Remember env vars are read at startup, so rotation needs a restart or file-based reload.
""", I, ["kubernetes", "secrets", "security"], False))

QA.append(("Explain the Kubernetes Service types and how external traffic reaches your pods. Where does Gateway API fit?", r"""
A **Service** gives a stable virtual IP and DNS name (`orders.payments.svc.cluster.local`) in front of a changing set of pods selected by labels.

- **ClusterIP** (default): reachable only inside the cluster. Used for service-to-service calls.
- **NodePort**: opens a port (30000-32767) on every node and forwards to the Service. Rarely used directly in production.
- **LoadBalancer**: asks the cloud provider for a load balancer (an NLB on AWS) per Service. Simple but costly when you have many services.
- **Headless** (`clusterIP: None`): DNS returns pod IPs directly, used by StatefulSets.

For HTTP, you usually expose one entry point and route by host/path:

- **Ingress** + an Ingress controller (AWS Load Balancer Controller creating an ALB, Traefik, NGINX-based controllers) handles TLS termination and routing rules.
- **Gateway API** is the newer, role-oriented successor (GatewayClass, Gateway, HTTPRoute), with richer features such as header matching and weighted traffic splitting for canaries. Since the community ingress-nginx controller was retired in March 2026, Kubernetes recommends Gateway API for new setups.

Flow: client -> DNS -> cloud LB -> gateway/ingress pods -> Service -> pod.
""", B, ["kubernetes", "networking", "ingress"], False))

QA.append(("Design a CI/CD pipeline for a Spring Boot microservice at a product company.", r"""
**On every pull request** (target < 10 minutes): compile, unit tests, Testcontainers integration tests against real MySQL/Kafka, static analysis (SpotBugs/Sonar), dependency vulnerability scan, secret scanning, and required code review.

**On merge to main:**
1. Build the image **once**, tagged with the **git SHA**; scan it; generate an SBOM; push to ECR.
2. Deploy to **dev** automatically; run contract tests (Pact) and API smoke tests.
3. Deploy to **staging**: smoke tests, a short load test for critical paths, Flyway migrations applied the same way as prod.
4. **Production**: progressive rollout (canary 5% -> 25% -> 100%) with automated analysis of error rate, p99 latency and a business metric; **automatic rollback** on breach.

**Principles to state:** the same artifact is promoted through environments (config differs, binary doesn't); pipeline defined as code in the repo; deploy credentials via OIDC federation, no stored cloud keys; migrations backward compatible (expand/contract); feature flags decouple deploy from release; every deploy is announced and traceable to a commit.

**Measure it** with DORA metrics: deployment frequency, lead time, change failure rate and time to restore. Mention what you'd do first at a small company: a reliable PR pipeline and one-click rollback beat a fancy canary setup.
""", I, ["ci-cd", "pipeline", "devops"], True))

QA.append(("Blue-green vs canary: when would you choose each, and how do you decide a canary is healthy?", r"""
**Blue-green**: run two full environments; deploy to idle "green", test it, then switch all traffic at once (load balancer or DNS). Rollback is instant: switch back. Good when you want a clean cutover, need to test the full stack before exposure, or traffic is too low for statistically meaningful canaries. Costs double capacity during the switch, and the **database is shared**, so schema changes must still be compatible with both.

**Canary**: shift a small percentage of real traffic (1-5%) to the new version, compare, then ramp up. Limits blast radius and catches issues that only appear with real traffic. Needs enough traffic, good metrics and tooling (Argo Rollouts, Flagger, weighted ALB target groups, Gateway API traffic splitting).

**Deciding canary health** (automate it):
- Compare canary vs **baseline** (same version as prod, same traffic share), not vs yesterday.
- Signals: 5xx rate, p95/p99 latency, saturation (CPU, pool usage), and at least one **business metric** (checkout success, payment authorisation rate).
- Fixed observation windows per step (e.g. 10 minutes), promotion only if all checks pass, automatic rollback otherwise.

**Watch out**: sticky sessions, cache key changes and async consumers running the new version can affect 100% of users even at 5% HTTP traffic.
""", I, ["deployment", "canary", "blue-green", "ci-cd"], True))

QA.append(("What are feature flags for, and what problems do they cause if handled badly?", r"""
Feature flags **decouple deployment from release**. Code ships to production switched off, then is enabled gradually (internal users, 1%, 10%, 100%) or instantly disabled without a deploy.

Uses:
- **Release toggles**: merge unfinished work into trunk safely; short-lived.
- **Ops toggles / kill switches**: turn off an expensive recommendation call during an incident.
- **Experiments**: A/B tests with consistent bucketing by user ID.
- **Permission toggles**: premium features or per-tenant enablement.

Problems when handled badly:
- **Flag debt**: hundreds of stale flags, dead code paths, and untested combinations. Give each flag an owner and an expiry date; remove it after full rollout.
- **Performance and availability**: evaluating flags with a remote call per request. Use an SDK with local caching and streaming updates, plus **safe defaults** if the flag service is unreachable.
- **Inconsistent behaviour**: a user flips between variants across pods because bucketing isn't deterministic.
- **False safety**: a flag can't undo irreversible side effects like a schema change or data already written in a new format.
- **Security**: authorization must not depend on a client-side flag.

Tools: LaunchDarkly, Unleash, Flagsmith, AWS AppConfig, or a simple DB-backed table for small teams. OpenFeature offers a vendor-neutral API.
""", I, ["feature-flags", "release", "ci-cd"], False))

QA.append(("A deploy at 6 pm broke checkout for 20% of users. Do you roll back or roll forward? What if the release included a DB migration?", r"""
**Default: roll back immediately.** Restoring service beats diagnosing in production. The previous image is known-good, and rollback should be one command (`kubectl rollout undo`, revert the Argo CD commit, or switch blue-green back). Communicate in the incident channel: impact, action, next update time.

**Roll forward only** if the fix is trivial and certain (a wrong config value) and faster than a rollback, or if rollback is unsafe.

**With a DB migration**, ask: is the old code compatible with the new schema?
- If the migration was **additive** (new nullable column, new table), old code ignores it: roll back the app and leave the schema.
- If it was **destructive or changed semantics** (dropped/renamed column, new enum values old code can't parse), rolling back the app breaks it too. Options: a forward fix, or a pre-written down-migration, carefully, because data written in between may be lost.

This is exactly why seniors insist on **expand/contract** migrations and decoupling schema deploys from code deploys: every step stays rollback-safe.

Afterwards: postmortem covering why the canary or tests didn't catch it, and a guardrail (automated canary analysis on checkout success rate, a contract test, a migration lint rule).
""", A, ["deployment", "rollback", "incident", "database"], True))

QA.append(("How do you change a database schema with no downtime, for example renaming a column used by a live service?", r"""
Never do a direct `ALTER TABLE ... RENAME COLUMN` while old code runs: during a rolling deploy, old pods would immediately fail. Use **expand and contract** in several backward-compatible deploys:

1. **Expand**: add the new column `customer_phone` (nullable, no default that locks the table). Old code is unaffected.
2. **Dual write**: deploy code that writes both `phone` and `customer_phone` but still reads `phone`.
3. **Backfill** existing rows in small batches (`UPDATE ... WHERE id BETWEEN ? AND ?`, throttled, off-peak) to avoid long locks and replication lag.
4. **Switch reads** to `customer_phone`, still writing both. Rollback remains safe.
5. **Contract**: stop writing `phone`, wait a release or two, then drop it.

For large MySQL tables, check whether the DDL is **instant/online** (MySQL 8 supports instant ADD COLUMN in many cases); otherwise use gh-ost or pt-online-schema-change to avoid long metadata locks. Run migrations through Flyway/Liquibase in the pipeline, with a lock timeout so a migration waiting on a lock doesn't block all queries behind it.

The same idea applies to API fields and event schemas: add first, migrate consumers, remove last.
""", A, ["database", "migrations", "zero-downtime", "mysql"], False))

QA.append(("What is a 12-factor app? Which factors matter most when you containerise a Spring Boot service?", r"""
The **12-factor app** is a methodology for building services that deploy cleanly to cloud platforms: one codebase, explicit dependencies, config in the environment, backing services as attached resources, separate build/release/run stages, stateless processes, port binding, scale out via processes, disposability, dev/prod parity, logs as event streams, and admin tasks as one-off processes.

The ones that bite hardest in containers:

- **Config (III)**: same image in every environment; values from env vars/ConfigMaps and secrets from a secret manager, not `application-prod.yml` with passwords baked in.
- **Stateless processes (VI)**: no in-memory HTTP sessions or local file uploads; pods are killed and rescheduled freely. Use Redis for sessions and S3 for files.
- **Disposability (IX)**: start fast, handle SIGTERM gracefully, make jobs idempotent so a killed pod's work can be retried.
- **Logs (XI)**: structured JSON to stdout; let the platform collect it.
- **Dev/prod parity (X)**: Testcontainers with real MySQL instead of H2.

A classic violation to mention: `@Scheduled` jobs running in every replica after scaling out. Fix with ShedLock, a Kubernetes CronJob, or a queue.
""", B, ["12-factor", "cloud-native", "spring-boot"], False))

QA.append(("What is Terraform state, why must it be remote and locked, and what is drift?", r"""
**State** is Terraform's record mapping each resource in your code to the real object it manages (IDs, attributes, dependencies). `plan` compares code, state and reality to compute changes.

**Remote** (S3, Terraform Cloud, GCS) because a local `terraform.tfstate` on a laptop can't be shared, gets lost, and leads to two people managing the same infrastructure from different files. **Locked** because two concurrent `apply` runs can corrupt state or make conflicting changes. S3 backends traditionally used a DynamoDB table for locks; recent Terraform versions support S3-native lock files (`use_lockfile = true`). State can contain **secrets** (DB passwords, keys), so encrypt it and restrict access.

**Drift** happens when real infrastructure differs from code, usually from manual console edits during an incident. The next `apply` may silently revert someone's emergency fix, or fail. Detect it with scheduled `terraform plan` runs that should show "No changes", and fix by importing the change into code or reverting it.

Good habits: plan on every PR and review it like code; protect critical resources with `lifecycle { prevent_destroy = true }`; split state per environment/component to reduce blast radius.
""", I, ["terraform", "iac", "devops"], False))

QA.append(("Your AWS bill for a modest backend has doubled in six months. How would you investigate and reduce it?", r"""
Treat it like a performance problem: **measure, find the top items, fix the biggest first.**

1. **Cost Explorer** grouped by service, then by usage type and tag. Make sure resources are tagged by team/service; untagged spend is a finding in itself.
2. Common hidden costs:
   - **NAT Gateway data processing**: S3/DynamoDB traffic through NAT. Fix: VPC gateway endpoints (free).
   - **Cross-AZ data transfer** from chatty services or replicas.
   - **CloudWatch Logs** ingestion and indefinite retention, often from DEBUG logging. Fix: log levels, retention policies, sampling.
   - **Over-provisioned RDS/EC2**: CPU at 5%. Right-size using utilisation data; move to Graviton (ARM) instances, which Java runs on well.
   - **Idle resources**: unused load balancers, unattached EBS volumes, old snapshots, forgotten dev environments.
   - **S3**: lifecycle rules to cheaper storage classes, clean incomplete multipart uploads.
3. **Commitment discounts** (Savings Plans, reserved instances) for the steady baseline; **Spot** for fault-tolerant batch work.
4. **Architecture**: cache hot reads, batch small writes, scale to zero in non-prod at night.

Then make it stick: budgets and anomaly alerts, cost per request/tenant as a tracked metric, and cost reviewed in design docs. Interviewers like hearing "cost is a non-functional requirement".
""", A, ["aws", "cost", "finops"], False))

QA.append(("How would you use ElastiCache (Redis/Valkey) in front of MySQL, and what happens when the cache node fails?", r"""
**Typical uses**: cache-aside for hot reads (product details, config), session storage, rate-limit counters, distributed locks with care, leaderboards (sorted sets), and idempotency keys with TTL.

**Cache-aside flow**: read from cache; on miss, read from MySQL, write to cache with a TTL; on update, write to MySQL then **delete** the cache key (deleting is safer than updating, to avoid racing writers). Add TTL jitter so keys don't expire together.

**When a node fails:**
- With **replication + automatic failover** (cluster mode or a replica group across AZs), a replica is promoted in seconds. Clients need reconnection and timeouts; recent writes may be lost because replication is async, so never keep data in the cache that you can't rebuild.
- If the cache is empty or unreachable, **every request hits MySQL**: the thundering herd can take down the database. Protections: short client timeouts and a circuit breaker so you degrade instead of hanging, request coalescing (only one loader per key), rate limiting at the edge, and capacity planning so the DB survives a cold cache for a while, or a warm-up job.

**Senior point**: test this failure deliberately. "Cache down equals DB down" is a design flaw, not bad luck. Also note Valkey is the open-source Redis fork that ElastiCache now supports.
""", I, ["aws", "elasticache", "redis", "caching"], False))

SOURCES = [
    ("AWS Decision Guide: Choosing an AWS container service", "https://docs.aws.amazon.com/decision-guides/latest/containers-on-aws-how-to-choose/choosing-aws-container-service.html"),
    ("AWS Well-Architected Framework", "https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html"),
    ("AWS Compute Blog: Reducing Java cold starts with Lambda SnapStart", "https://aws.amazon.com/blogs/compute/reducing-java-cold-starts-on-aws-lambda-functions-with-snapstart/"),
    ("Spring Boot reference: Dockerfiles and efficient container images", "https://docs.spring.io/spring-boot/reference/packaging/container-images/dockerfiles.html"),
    ("Docker docs: Building best practices", "https://docs.docker.com/build/building/best-practices/"),
    ("Kubernetes docs: Resource management for pods and containers", "https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/"),
    ("Kubernetes docs: Configure liveness, readiness and startup probes", "https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/"),
    ("Kubernetes docs: Horizontal Pod Autoscaling", "https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/"),
    ("Kubernetes blog: Ingress NGINX retirement (Nov 2025)", "https://kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/"),
    ("The Twelve-Factor App", "https://12factor.net/"),
    ("Martin Fowler: Feature Toggles", "https://martinfowler.com/articles/feature-toggles.html"),
    ("Martin Fowler: Blue-Green Deployment", "https://martinfowler.com/bliki/BlueGreenDeployment.html"),
    ("Terraform docs: S3 backend (state locking)", "https://developer.hashicorp.com/terraform/language/backend/s3"),
    ("DORA research program", "https://dora.dev/"),
]


def subject():
    return build("cloud-devops", "Cloud, Docker, Kubernetes & CI/CD", 16, "☁️",
                 "The AWS, Docker, Kubernetes and CI/CD knowledge a senior backend engineer must reason about: which managed service and why, production-grade containers, and safe releases.",
                 "cloud", NOTES, QA, SOURCES)


if __name__ == "__main__":
    report(subject())
