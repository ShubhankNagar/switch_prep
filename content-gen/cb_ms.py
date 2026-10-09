from cb_common import build
from cb_ms_notes import NOTES
from cb_ms_qa import QA
SOURCES = [
 ("Microservices.io - Pattern Language (Chris Richardson)", "https://microservices.io/patterns/index.html"),
 ("Martin Fowler - Microservices", "https://martinfowler.com/articles/microservices.html"),
 ("Spring Cloud Documentation", "https://spring.io/projects/spring-cloud"),
 ("Resilience4j Documentation", "https://resilience4j.readme.io/docs"),
 ("Apache Kafka Documentation", "https://kafka.apache.org/documentation/"),
 ("Spring for Apache Kafka Reference", "https://docs.spring.io/spring-kafka/reference/"),
 ("Micrometer Tracing Documentation", "https://docs.micrometer.io/tracing/reference/"),
 ("Kubernetes Documentation - Concepts", "https://kubernetes.io/docs/concepts/"),
 ("Docker Docs - Dockerfile best practices", "https://docs.docker.com/build/building/best-practices/"),
 ("Debezium - Outbox Event Router", "https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html"),
 ("The Twelve-Factor App", "https://12factor.net/"),
 ("GeeksforGeeks - Microservices Interview Questions", "https://www.geeksforgeeks.org/system-design/microservices-interview-questions/"),
]
build("microservices", "Microservices & Distributed Systems", 3, "🧩", "Designing, connecting, securing, observing and deploying Spring-based microservices with Kafka, Resilience4j, Docker and Kubernetes.", NOTES, QA, SOURCES)
