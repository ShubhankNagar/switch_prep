from cb_common import build
from cb_spring_notes import NOTES
from cb_spring_qa import QA
SOURCES = [
 ("Spring Framework Reference Documentation", "https://docs.spring.io/spring-framework/reference/"),
 ("Spring Boot Reference Documentation", "https://docs.spring.io/spring-boot/reference/"),
 ("Spring Data JPA Reference", "https://docs.spring.io/spring-data/jpa/reference/"),
 ("Spring Security Reference - Servlet Architecture", "https://docs.spring.io/spring-security/reference/servlet/architecture.html"),
 ("Baeldung - Spring @Transactional", "https://www.baeldung.com/transaction-configuration-with-jpa-and-spring"),
 ("Baeldung - Spring Bean Scopes", "https://www.baeldung.com/spring-bean-scopes"),
 ("Vlad Mihalcea - N+1 Query Problem", "https://vladmihalcea.com/n-plus-1-query-problem/"),
 ("Hibernate ORM User Guide", "https://docs.jboss.org/hibernate/orm/6.6/userguide/html_single/Hibernate_User_Guide.html"),
 ("GeeksforGeeks - Spring Boot Interview Questions", "https://www.geeksforgeeks.org/advance-java/spring-boot-interview-questions-and-answers/"),
 ("InterviewBit - Spring Boot Interview Questions", "https://www.interviewbit.com/spring-boot-interview-questions/"),
 ("Testcontainers for Java", "https://java.testcontainers.org/"),
]
build("spring-boot", "Spring & Spring Boot", 2, "🌱", "Spring IoC, Boot auto-configuration, REST, JPA/Hibernate, transactions, security, testing and production features.", NOTES, QA, SOURCES)
