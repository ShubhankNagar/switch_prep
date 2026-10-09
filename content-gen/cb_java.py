from cb_common import build
from cb_java_notes import NOTES
from cb_java_qa import QA
SOURCES = [
 ("Oracle Java SE Documentation", "https://docs.oracle.com/en/java/javase/21/"),
 ("OpenJDK JEP Index", "https://openjdk.org/jeps/0"),
 ("Baeldung - Java HashMap Guide", "https://www.baeldung.com/java-hashmap"),
 ("Baeldung - Guide to ConcurrentHashMap", "https://www.baeldung.com/java-concurrent-map"),
 ("Baeldung - Java 8 Streams", "https://www.baeldung.com/java-8-streams"),
 ("Baeldung - Virtual Threads", "https://www.baeldung.com/java-virtual-thread-vs-thread"),
 ("Oracle - Garbage Collection Tuning Guide (G1, ZGC)", "https://docs.oracle.com/en/java/javase/21/gctuning/"),
 ("GeeksforGeeks - Java Interview Questions", "https://www.geeksforgeeks.org/java/java-interview-questions/"),
 ("InterviewBit - Java Interview Questions", "https://www.interviewbit.com/java-interview-questions/"),
 ("LeetCode Discuss - Interview Experiences", "https://leetcode.com/discuss/interview-experience"),
 ("Java Concurrency in Practice (Goetz et al.)", "https://jcip.net/"),
]
build("java", "Core Java", 1, "☕", "Core Java from OOP and collections internals to streams, modern Java 21 features, concurrency and JVM internals.", NOTES, QA, SOURCES)
