from ai2_common import Q, R, L, M

lessons = [
L("m13-spring-ai-chatclient", "Spring AI Fundamentals: Setup and ChatClient", 50, r"""
## Why Spring AI matters for you

Most enterprise backends in India and elsewhere run on Java. Companies adding AI to existing Spring Boot systems want engineers who know **both** worlds. **Spring AI** is the official Spring project for AI integration: portable APIs over chat, embedding, image and audio models from many providers (OpenAI, Anthropic, Google, Azure OpenAI, Amazon Bedrock, Mistral, Ollama and more), vector stores, RAG, tool calling, chat memory, MCP and observability. Everything you learned in Python maps onto familiar Spring concepts: auto-configuration, starters, beans, builders, `application.yml`.

(The other notable Java option is **LangChain4j**; concepts transfer between them.)

### Concept map: Python -> Spring AI

| Python (modules 7-12) | Spring AI |
|----------------------|-----------|
| `anthropic` / `openai` SDK client | `ChatModel` bean (auto-configured by a starter) |
| Your `LlmClient` wrapper | `ChatClient` fluent API |
| Prompt templates (Jinja/f-strings) | `PromptTemplate` with `{placeholders}` |
| Pydantic structured output | `.entity(MyRecord.class)` |
| Embeddings + pgvector | `EmbeddingModel` + `VectorStore` (PgVectorStore) |
| RAG pipeline | `QuestionAnswerAdvisor` / `RetrievalAugmentationAdvisor` |
| Tool-calling loop | `@Tool` methods + `.tools(...)`, loop handled for you |
| Chat history | `ChatMemory` + `MessageChatMemoryAdvisor` |
| MCP SDK | MCP client/server Boot starters |
| Tracing | Micrometer observations + Actuator |

### Project setup

Create a project on start.spring.io with Spring Web plus an AI model starter, or add the Spring AI BOM and a starter manually. Use the Spring AI version compatible with your Spring Boot version (the 1.x line targets Spring Boot 3.x; check the project's compatibility notes for newer lines).

```xml
<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>org.springframework.ai</groupId>
      <artifactId>spring-ai-bom</artifactId>
      <version>${spring-ai.version}</version>
      <type>pom</type>
      <scope>import</scope>
    </dependency>
  </dependencies>
</dependencyManagement>

<dependencies>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
  </dependency>
  <dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-model-anthropic</artifactId>   <!-- or -openai, -ollama ... -->
  </dependency>
</dependencies>
```

```yaml
# application.yml
spring:
  ai:
    anthropic:
      api-key: ${ANTHROPIC_API_KEY}
      chat:
        options:
          model: claude-sonnet-4-5      # current model id from provider docs
          temperature: 0.3
          max-tokens: 800
```

Want it free and local? Swap to `spring-ai-starter-model-ollama` with `spring.ai.ollama.chat.options.model: qwen2.5:7b`. Your code doesn't change: that's the portability benefit.

### ChatClient: the fluent API

`ChatClient` is to LLMs what `RestClient`/`WebClient` is to HTTP. Spring Boot auto-configures a `ChatClient.Builder`:

```java
@RestController
@RequestMapping("/api/ai")
class MentorController {

    private final ChatClient chatClient;

    MentorController(ChatClient.Builder builder) {
        this.chatClient = builder
                .defaultSystem("You are a concise mentor for Java developers learning AI engineering.")
                .build();
    }

    @GetMapping("/ask")
    String ask(@RequestParam String question) {
        return chatClient.prompt()
                .user(question)
                .call()
                .content();                     // just the text
    }
}
```

Need metadata (tokens, finish reason, model)? Use `.call().chatResponse()`:

```java
ChatResponse resp = chatClient.prompt().user(question).call().chatResponse();
Usage usage = resp.getMetadata().getUsage();
log.info("tokens in={} out={}", usage.getPromptTokens(), usage.getCompletionTokens());
String text = resp.getResult().getOutput().getText();
```

Override options per request:

```java
chatClient.prompt()
    .user("Classify: " + ticket)
    .options(ChatOptions.builder().temperature(0.0).maxTokens(20).build())
    .call().content();
```

### Streaming

```java
@GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
Flux<String> stream(@RequestParam String question) {
    return chatClient.prompt().user(question).stream().content();
}
```

`stream()` returns a Reactor `Flux<String>` of token chunks. Spring MVC can return a `Flux` as SSE (add `spring-boot-starter-webflux` to the classpath for Reactor, or build the whole app on WebFlux). Lesson 7 connects this to Angular.

### Chat memory (multi-turn)

Remember from module 7: APIs are stateless. Spring AI's `ChatMemory` stores history per conversation id, and an **advisor** injects it into each request:

```java
@Bean
ChatClient chatClient(ChatClient.Builder builder, ChatMemory chatMemory) {
    return builder
        .defaultSystem("You are a helpful assistant.")
        .defaultAdvisors(MessageChatMemoryAdvisor.builder(chatMemory).build())
        .build();
}

// per request: scope memory to the user's conversation
String reply = chatClient.prompt()
    .user(message)
    .advisors(a -> a.param(ChatMemory.CONVERSATION_ID, conversationId))
    .call().content();
```

The default auto-configured `ChatMemory` keeps a sliding window of recent messages in memory; JDBC and other repositories persist it in your database.

### Advisors: Spring AI's interceptors

**Advisors** wrap the call like servlet filters or Spring AOP around-advice: they can modify the request (add memory, retrieved documents) and inspect the response (logging, safety checks). Built-ins include memory advisors, `QuestionAnswerAdvisor` (RAG), `SimpleLoggerAdvisor` and `SafeGuardAdvisor`. You can write your own by implementing `CallAdvisor`/`StreamAdvisor`.

### Python vs Java: same request

```python
# Python (module 7)
client.messages.create(model=MODEL, max_tokens=800, system=SYS,
                       messages=[{"role": "user", "content": q}]).content[0].text
```

```java
// Spring AI
chatClient.prompt().system(SYS).user(q).call().content();
```

### Key takeaways
- Spring AI gives portable, auto-configured model clients; switching providers is a dependency + config change.
- `ChatClient` is the fluent entry point: `.prompt().system().user().call().content()` or `.stream()`.
- Advisors add cross-cutting behaviour (memory, RAG, logging) like interceptors.
- Your Spring skills (config, DI, testing, Actuator) apply directly.
""", r"""
1. Create a Spring Boot project with Spring AI and one model starter (Ollama if you want zero cost). Implement `/api/ai/ask` and `/api/ai/stream`.
2. Add `MessageChatMemoryAdvisor` with a `conversationId` request parameter and verify multi-turn memory per conversation.
3. Log token usage per request from `ChatResponse` metadata.
4. Switch providers (e.g. Ollama -> OpenAI or Anthropic) by changing only dependencies and `application.yml`. Note any behaviour differences.
""", [
Q("What does `chatClient.prompt().user(q).call().content()` return?", ["A Flux of tokens", "The generated text as a String", "A ChatResponse with metadata", "An embedding"], 1, "content() extracts the text; chatResponse() gives metadata."),
Q("What is an Advisor in Spring AI?", ["A human reviewer", "An interceptor around ChatClient calls that can modify requests and responses (memory, RAG, logging)", "A vector database", "A model provider"], 1, "Advisors provide cross-cutting behaviour like filters/AOP."),
Q("How do you switch a Spring AI app from OpenAI to Ollama?", ["Rewrite all controllers", "Change the starter dependency and configuration properties", "It's impossible", "Use a different JDK"], 1, "Portable abstractions make providers swappable via dependencies and config."),
], [
R("Spring AI reference documentation", "https://docs.spring.io/spring-ai/reference/", "docs"),
R("Spring AI - ChatClient API", "https://docs.spring.io/spring-ai/reference/api/chatclient.html", "docs"),
R("Spring AI - Chat Memory", "https://docs.spring.io/spring-ai/reference/api/chat-memory.html", "docs"),
R("Spring AI examples (GitHub)", "https://github.com/spring-projects/spring-ai-examples", "docs"),
]),

L("m13-templates-structured-output", "Prompt Templates and Structured Output in Java", 40, r"""
## Prompt templates

Hard-coding prompts in string concatenation gets messy. Spring AI's `PromptTemplate` uses `{placeholder}` syntax (backed by the StringTemplate engine) and works with `ChatClient` directly:

```java
String answer = chatClient.prompt()
    .user(u -> u.text(<<TQ>>
            Explain {topic} to a Java developer with {years} years of experience.
            Use one analogy from Spring Boot. Max {words} words.
            <<TQ>>)
        .param("topic", "vector databases")
        .param("years", 2)
        .param("words", 150))
    .call().content();
```

Store prompts as resources and inject them, so prompt changes don't require Java edits (and can be versioned separately):

```java
@Value("classpath:/prompts/classify-ticket-v3.st")
private Resource classifyPrompt;

String label = chatClient.prompt()
    .system(s -> s.text(classifyPrompt).param("labels", "BILLING, DELIVERY, RETURNS, OTHER"))
    .user(ticketText)
    .options(ChatOptions.builder().temperature(0.0).build())
    .call().content();
```

Same best practices as module 7: delimit untrusted input, give an "I don't know" path, keep examples in the template, version files (`-v3`).

### Structured output: `.entity()`

This is where Java shines. Define a **record** and ask for it directly; Spring AI generates JSON Schema format instructions from the type, calls the model, and deserialises with Jackson:

```java
record Invoice(
    String vendor,
    String invoiceNumber,
    @JsonPropertyDescription("Grand total including tax") BigDecimal totalAmount,
    Currency currency,
    List<String> lineItems) {}

enum Currency { INR, USD, EUR }

Invoice invoice = chatClient.prompt()
    .system("Extract invoice fields. Use null for anything not present.")
    .user(invoiceText)
    .call()
    .entity(Invoice.class);
```

Generic types need a `ParameterizedTypeReference`:

```java
record Skill(String name, String level) {}

List<Skill> skills = chatClient.prompt()
    .user("Extract skills with level (beginner/intermediate/advanced) from this resume:\n" + resume)
    .call()
    .entity(new ParameterizedTypeReference<List<Skill>>() {});
```

Under the hood this uses `BeanOutputConverter`. You can also use `MapOutputConverter` / `ListOutputConverter` for loose shapes.

### Native structured output

By default the converter appends format instructions to the prompt, which works with any model but isn't guaranteed. Many providers support **schema-enforced** output (module 7). Spring AI can pass the generated JSON schema through provider options so the model is constrained, for example OpenAI's `responseFormat` with a JSON schema, and newer Spring AI versions offer a portable native structured-output switch for supporting models. Check the "Structured Output" page for your version and provider; prefer native mode when available.

### Validation and retries

The model can still return wrong *values*. Combine with Bean Validation, just like a REST DTO:

```java
record JobPosting(
    @NotBlank String title,
    @NotBlank String company,
    @Min(0) @Max(30) Integer minYearsExperience,
    @NotEmpty List<String> skills) {}

@Service
class Extractor {
    private final ChatClient chat;
    private final Validator validator;

    Extractor(ChatClient.Builder b, Validator v) { this.chat = b.build(); this.validator = v; }

    JobPosting extract(String text) {
        String feedback = "";
        for (int attempt = 0; attempt < 3; attempt++) {
            JobPosting p = chat.prompt()
                .system("Extract the job posting. Use null when unknown.")
                .user(text + feedback)
                .call().entity(JobPosting.class);
            var errors = validator.validate(p);
            if (errors.isEmpty()) return p;
            feedback = "\n\nYour previous answer had errors, fix them: " + errors.stream()
                .map(e -> e.getPropertyPath() + " " + e.getMessage()).toList();
        }
        throw new IllegalStateException("Extraction failed validation");
    }
}
```

Spring AI also supports retries for transient API errors via its retry auto-configuration (`spring.ai.retry.*` properties).

### Testing AI code in Spring

- **Unit tests**: mock `ChatModel` (or the `ChatClient`) to test your service logic deterministically.
- **Integration tests**: run against Ollama in Testcontainers or a real API behind a profile.
- **Evals**: Spring AI includes evaluator abstractions (e.g. `RelevancyEvaluator`, `FactCheckingEvaluator`) that use an LLM to judge responses, which you can run in JUnit as an eval suite. The principles from module 12 apply: validate judges, use fixed datasets.

```java
@Test
void classifiesRefundTickets() {
    var cases = Map.of("Money not refunded after return", "RETURNS",
                       "Charged twice for one order", "BILLING");
    cases.forEach((text, expected) ->
        assertThat(classifier.classify(text)).isEqualTo(expected));
}
```

### Python vs Java side by side

```python
inv = client.responses.parse(model=M, input=text, text_format=Invoice).output_parsed
```

```java
Invoice inv = chatClient.prompt().user(text).call().entity(Invoice.class);
```

### Key takeaways
- Use `PromptTemplate`-style `.text(...).param(...)` and keep prompts as versioned resource files.
- `.entity(Record.class)` maps responses to records; use `ParameterizedTypeReference` for generics.
- Prefer provider-native schema enforcement when available; still validate with Bean Validation and retry with feedback.
- Mock models for unit tests; run eval suites as integration tests.
""", r"""
1. Build `POST /api/extract/job` that returns a `JobPosting` record from pasted job-description text, with Bean Validation and a feedback retry loop.
2. Move all prompts to `src/main/resources/prompts/*.st` and inject them as `Resource`.
3. Write JUnit tests with a mocked model for the service logic, and a separate `@Tag("eval")` test running 10 real job descriptions against a live model.
4. Compare `.entity()` results for prompt-only vs native schema-enforced output (if your provider supports it) on the same 10 inputs.
""", [
Q("How does Spring AI's `.entity(Invoice.class)` work by default?", ["It fine-tunes the model", "It adds JSON format instructions derived from the type, then deserialises the response with Jackson", "It queries a database", "It uses reflection on the model weights"], 1, "BeanOutputConverter generates schema instructions and parses the result."),
Q("How do you get a `List<Skill>` from ChatClient?", ["entity(List.class)", "entity(new ParameterizedTypeReference<List<Skill>>() {})", "content().split()", "It's not possible"], 1, "Generic types need a ParameterizedTypeReference."),
Q("What's a good way to unit test a service that uses an LLM?", ["Always call the real API", "Mock the ChatModel/ChatClient to return fixed responses", "Skip tests", "Use temperature 0 on the real API"], 1, "Mocks make business logic tests fast and deterministic; real-model evals run separately."),
], [
R("Spring AI - Structured Output Converter", "https://docs.spring.io/spring-ai/reference/api/structured-output-converter.html", "docs"),
R("Spring AI - Prompts and PromptTemplate", "https://docs.spring.io/spring-ai/reference/api/prompt.html", "docs"),
R("Spring AI - Evaluation testing", "https://docs.spring.io/spring-ai/reference/api/testing.html", "docs"),
]),

L("m13-embeddings-pgvector", "Embeddings and PgVector in Spring Boot", 45, r"""
## The Spring AI retrieval stack

Spring AI gives you the same pieces you built in Python in module 8, as beans:
- `EmbeddingModel`: turns text into vectors (OpenAI, Ollama, Vertex, Bedrock, ONNX local models, etc.).
- `Document`: text + metadata + id (Spring AI's chunk).
- `VectorStore`: portable API over pgvector, Qdrant, Chroma, Redis, Elasticsearch, Pinecone, Weaviate, MongoDB Atlas, Neo4j, Oracle, and more.
- An **ETL pipeline**: `DocumentReader` -> `DocumentTransformer` (e.g. `TokenTextSplitter`) -> `DocumentWriter` (the vector store).

Because you already know Postgres/MySQL and JPA, pgvector is the natural choice.

### Dependencies and config

```xml
<dependency>
  <groupId>org.springframework.ai</groupId>
  <artifactId>spring-ai-starter-vector-store-pgvector</artifactId>
</dependency>
<dependency>
  <groupId>org.springframework.ai</groupId>
  <artifactId>spring-ai-starter-model-openai</artifactId>   <!-- for embeddings; or -ollama -->
</dependency>
<dependency>
  <groupId>org.springframework.ai</groupId>
  <artifactId>spring-ai-tika-document-reader</artifactId>   <!-- PDFs, DOCX, HTML... -->
</dependency>
```

```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/ai
    username: postgres
    password: ${DB_PASSWORD}
  ai:
    openai:
      api-key: ${OPENAI_API_KEY}
      embedding:
        options:
          model: text-embedding-3-small
    vectorstore:
      pgvector:
        initialize-schema: true      # creates extension + table (use migrations in prod)
        index-type: HNSW
        distance-type: COSINE_DISTANCE
        dimensions: 1536             # must match the embedding model
```

Run Postgres with pgvector: `docker run -p 5432:5432 -e POSTGRES_PASSWORD=pw -e POSTGRES_DB=ai pgvector/pgvector:pg17`.

If chat uses Anthropic (which has no embedding API), use OpenAI, Ollama or another provider's starter for embeddings. Spring lets you mix models from different providers in one app.

### Embedding directly

```java
@Service
class EmbeddingDemo {
    private final EmbeddingModel embeddingModel;
    EmbeddingDemo(EmbeddingModel m) { this.embeddingModel = m; }

    double similarity(String a, String b) {
        float[] va = embeddingModel.embed(a);
        float[] vb = embeddingModel.embed(b);
        double dot = 0, na = 0, nb = 0;
        for (int i = 0; i < va.length; i++) { dot += va[i]*vb[i]; na += va[i]*va[i]; nb += vb[i]*vb[i]; }
        return dot / (Math.sqrt(na) * Math.sqrt(nb));
    }
}
```

### The ingestion (ETL) pipeline

```java
@Service
class IngestionService {
    private final VectorStore vectorStore;
    IngestionService(VectorStore vs) { this.vectorStore = vs; }

    public int ingest(Resource file, String tenantId, String docId) {
        List<Document> raw = new TikaDocumentReader(file).get();           // extract text
        List<Document> chunks = TokenTextSplitter.builder()
                .withChunkSize(500)                                          // tokens
                .build()
                .apply(raw);
        chunks.forEach(d -> {
            d.getMetadata().put("tenantId", tenantId);
            d.getMetadata().put("docId", docId);
            d.getMetadata().put("source", file.getFilename());
        });
        vectorStore.add(chunks);                                             // embeds + stores
        return chunks.size();
    }

    public void deleteDocument(String docId) {
        vectorStore.delete("docId == '" + docId + "'");                    // filter-expression delete
    }
}
```

(Builder method names differ slightly between versions; constructor forms like `new TokenTextSplitter()` also exist.) `vectorStore.add` calls the `EmbeddingModel` in batches and writes rows to the `vector_store` table: id, content, metadata (JSONB), embedding.

Other readers: `TextReader`, `JsonReader`, `PagePdfDocumentReader`/`ParagraphPdfDocumentReader`, `MarkdownDocumentReader`. Add contextual headers (title, section) to chunk text as you did in module 8.

### Similarity search with filters

```java
List<Document> results = vectorStore.similaritySearch(
    SearchRequest.builder()
        .query("How do I configure the connection pool?")
        .topK(5)
        .similarityThreshold(0.5)
        .filterExpression("tenantId == 'acme' && source in ['hikari.md', 'datasource.md']")
        .build());

results.forEach(d -> System.out.println(d.getScore() + " " + d.getMetadata().get("source")));
```

The filter expression is a portable SQL-like DSL translated to each store's native filter (for pgvector, a JSONB path query). You can also build filters type-safely with `FilterExpressionBuilder`. As in module 9, **derive the tenant from the authenticated user** (Spring Security context), never from the request body.

### Hybrid search and reranking in Java

Spring AI's portable `VectorStore` API focuses on vector search. For hybrid search on Postgres, add a `tsvector` column and run the RRF SQL from module 8 via `JdbcTemplate`, or use a store with native hybrid support (Elasticsearch/OpenSearch, Weaviate, Qdrant). Rerankers can be called via provider APIs (e.g. Cohere) in a custom `DocumentPostProcessor` in the RAG pipeline (next lesson).

### Production notes
- Use Flyway/Liquibase to create the pgvector extension, table and indexes instead of `initialize-schema` in production.
- Run ingestion as an async job (`@Async`, Spring Batch or a Kafka consumer) not in the HTTP request.
- Store a content hash per document to skip unchanged files on re-ingest.
- Record the embedding model name; changing it requires re-embedding everything.

### Key takeaways
- Spring AI's ETL: DocumentReader -> TokenTextSplitter -> VectorStore.add (embeds automatically).
- PgVectorStore stores content, JSONB metadata and vectors; configure index type, distance and dimensions.
- `SearchRequest` supports topK, threshold and portable filter expressions; enforce tenancy from security context.
- Treat ingestion as a background job with migrations, hashing and model tracking.
""", r"""
1. Add pgvector + an embedding starter to your Spring Boot app. Implement `POST /api/docs` (multipart upload) that ingests a PDF/Markdown file with tenant and doc metadata.
2. Implement `GET /api/search?q=` returning top-5 chunks with scores, filtered by the tenant from a (mock) authenticated principal.
3. Implement `DELETE /api/docs/{docId}` and re-ingestion that replaces old chunks.
4. Inspect the `vector_store` table in psql: look at the metadata JSONB and the index definition.
""", [
Q("In Spring AI, what does `vectorStore.add(documents)` do?", ["Only stores text", "Embeds the documents with the configured EmbeddingModel and stores content, metadata and vectors", "Trains a model", "Deletes old data"], 1, "The store calls the embedding model and writes the results."),
Q("What must `spring.ai.vectorstore.pgvector.dimensions` match?", ["The number of documents", "The output dimension of the embedding model", "The chunk size", "The topK value"], 1, "Vector column size must equal the embedding dimension."),
Q("Where should the tenant filter value come from?", ["The request JSON body", "The authenticated user in the Spring Security context", "The LLM's answer", "A random UUID"], 1, "Access control must derive from trusted authentication."),
], [
R("Spring AI - Vector Databases", "https://docs.spring.io/spring-ai/reference/api/vectordbs.html", "docs"),
R("Spring AI - PGvector store", "https://docs.spring.io/spring-ai/reference/api/vectordbs/pgvector.html", "docs"),
R("Spring AI - ETL Pipeline", "https://docs.spring.io/spring-ai/reference/api/etl-pipeline.html", "docs"),
R("Spring AI - Embeddings API", "https://docs.spring.io/spring-ai/reference/api/embeddings.html", "docs"),
]),

L("m13-rag-advisors", "RAG in Spring Boot with Advisors", 45, r"""
## RAG the Spring way

In module 9 you hand-wrote: retrieve -> build context -> prompt -> generate. Spring AI packages this as **advisors** that plug into `ChatClient`. Two levels:

1. `QuestionAnswerAdvisor`: simple, ready-made naive RAG.
2. `RetrievalAugmentationAdvisor`: a modular pipeline with query transformers, expanders, retrievers, post-processors and augmenters, which is advanced RAG.

### QuestionAnswerAdvisor in 10 lines

```xml
<dependency>
  <groupId>org.springframework.ai</groupId>
  <artifactId>spring-ai-advisors-vector-store</artifactId>
</dependency>
```

(Artifact names occasionally change between releases; check the RAG page of the reference docs for your version.)

```java
@RestController
class DocsChatController {
    private final ChatClient chatClient;

    DocsChatController(ChatClient.Builder builder, VectorStore vectorStore) {
        this.chatClient = builder
            .defaultSystem(<<TQ>>
                You answer questions about ACME engineering docs.
                If the context doesn't contain the answer, say you don't know.<<TQ>>)
            .defaultAdvisors(QuestionAnswerAdvisor.builder(vectorStore)
                .searchRequest(SearchRequest.builder().topK(6).similarityThreshold(0.5).build())
                .build())
            .build();
    }

    @GetMapping("/api/docs/ask")
    String ask(@RequestParam String q) {
        return chatClient.prompt().user(q).call().content();
    }
}
```

The advisor embeds the question, searches the store, appends the retrieved documents to the user message with instructions to use them, and forwards the call.

### Per-request filters (multi-tenancy)

```java
String answer = chatClient.prompt()
    .user(q)
    .advisors(a -> a.param(QuestionAnswerAdvisor.FILTER_EXPRESSION,
                           "tenantId == '" + currentUser.tenantId() + "'"))
    .call().content();
```

Build the filter from the authenticated principal. Since this is a string expression, never interpolate raw user input into it; use values from trusted sources or `FilterExpressionBuilder`.

### Returning sources (citations)

Retrieved documents are available in the response context so you can show sources:

```java
ChatClientResponse r = chatClient.prompt().user(q).call().chatClientResponse();
@SuppressWarnings("unchecked")
List<Document> docs = (List<Document>) r.context().get(QuestionAnswerAdvisor.RETRIEVED_DOCUMENTS);
String text = r.chatResponse().getResult().getOutput().getText();
List<String> sources = docs.stream().map(d -> (String) d.getMetadata().get("source")).distinct().toList();
return new AnswerDto(text, sources);
```

(The exact accessor names vary slightly across Spring AI versions; the idea is that the retrieved documents travel in the advisor context.)

### Modular RAG: RetrievalAugmentationAdvisor

```xml
<dependency>
  <groupId>org.springframework.ai</groupId>
  <artifactId>spring-ai-rag</artifactId>
</dependency>
```

```java
Advisor rag = RetrievalAugmentationAdvisor.builder()
    // 1. pre-retrieval: rewrite the query (module 9 lesson 3)
    .queryTransformers(RewriteQueryTransformer.builder()
        .chatClientBuilder(builder.build().mutate())
        .build())
    // 2. retrieval
    .documentRetriever(VectorStoreDocumentRetriever.builder()
        .vectorStore(vectorStore)
        .similarityThreshold(0.5)
        .topK(8)
        .build())
    // 3. generation: allow "I don't know" when nothing is retrieved
    .queryAugmenter(ContextualQueryAugmenter.builder()
        .allowEmptyContext(false)
        .build())
    .build();

String answer = chatClient.prompt().advisors(rag).user(q).call().content();
```

Building blocks you'll recognise:
- **Query transformers**: `RewriteQueryTransformer`, `CompressionQueryTransformer` (condense chat history into a standalone query), `TranslationQueryTransformer`.
- **Query expander**: `MultiQueryExpander` (multi-query retrieval).
- **Document retriever**: `VectorStoreDocumentRetriever` with filter expressions.
- **Document joiner**: merges results from multiple queries/sources.
- **Post-processing**: plug in reranking, deduplication or compression.
- **Query augmenter**: `ContextualQueryAugmenter` builds the final prompt with context and handles empty context.

### Combining RAG and memory

Advisors compose. Order matters, like a filter chain:

```java
this.chatClient = builder
    .defaultAdvisors(
        MessageChatMemoryAdvisor.builder(chatMemory).build(),   // adds history
        rag,                                                     // adds retrieved docs
        new SimpleLoggerAdvisor())                               // logs request/response
    .build();
```

For conversational RAG, add `CompressionQueryTransformer` so follow-ups ("and for MySQL?") are rewritten into standalone queries before retrieval.

### Evaluating RAG in JUnit

```java
@Test
void answersAreRelevantToRetrievedContext() {
    var evaluator = new RelevancyEvaluator(ChatClient.builder(judgeModel));
    String q = "How do I set the Hikari max pool size?";
    ChatClientResponse r = chatClient.prompt().user(q).call().chatClientResponse();
    List<Document> ctx = (List<Document>) r.context().get(QuestionAnswerAdvisor.RETRIEVED_DOCUMENTS);
    var result = evaluator.evaluate(new EvaluationRequest(q, ctx,
            r.chatResponse().getResult().getOutput().getText()));
    assertThat(result.isPass()).isTrue();
}
```

Extend it with your module 12 dataset: loop over cases, compute pass rates, and fail the build below a threshold.

### Key takeaways
- `QuestionAnswerAdvisor` = naive RAG in a few lines; pass filter expressions per request for tenancy.
- `RetrievalAugmentationAdvisor` composes query transformation, expansion, retrieval, post-processing and augmentation.
- Advisors chain with memory and logging; order matters.
- Surface retrieved documents as citations and evaluate with Spring AI evaluators or your own harness.
""", r"""
1. Add `QuestionAnswerAdvisor` to your app from the previous lesson and return `{answer, sources}` JSON.
2. Replace it with a `RetrievalAugmentationAdvisor` using `CompressionQueryTransformer` + memory so follow-up questions work. Test 5 two-turn conversations.
3. Configure `allowEmptyContext(false)` and verify unanswerable questions get a polite "don't know".
4. Port 20 eval cases from module 9 into a JUnit eval test that reports a pass rate using `RelevancyEvaluator` or your own judge.
""", [
Q("What does QuestionAnswerAdvisor do?", ["Fine-tunes the model on documents", "Retrieves relevant documents from the VectorStore and adds them to the prompt before calling the model", "Creates embeddings for the user", "Logs requests only"], 1, "It implements naive RAG as an advisor."),
Q("Which component would rewrite a follow-up question using chat history in Spring AI's modular RAG?", ["ContextualQueryAugmenter", "CompressionQueryTransformer", "TokenTextSplitter", "PgVectorStore"], 1, "Compression transformers condense history + follow-up into a standalone query."),
Q("Why does advisor order matter?", ["It doesn't", "Advisors form a chain; each modifies the request/response in sequence, like filters", "Only the first advisor runs", "Order changes the model"], 1, "Like a filter chain, the sequence determines how context is assembled."),
], [
R("Spring AI - Retrieval Augmented Generation", "https://docs.spring.io/spring-ai/reference/api/retrieval-augmented-generation.html", "docs"),
R("Spring AI - Advisors API", "https://docs.spring.io/spring-ai/reference/api/advisors.html", "docs"),
R("Spring blog - Spring AI posts and release notes", "https://spring.io/blog/category/engineering", "article"),
]),

L("m13-tool-calling", "Tool Calling in Spring AI", 40, r"""
## Tools as annotated Java methods

In module 7 you wrote the tool loop by hand: send tool schemas, detect tool calls, execute, send results, repeat. Spring AI does all of that for you. You write ordinary Spring beans with `@Tool` methods; the framework generates JSON schemas from the method signatures, runs the loop and invokes your methods.

```java
@Component
class OrderTools {

    private final OrderRepository orders;
    OrderTools(OrderRepository orders) { this.orders = orders; }

    @Tool(description = "Get shipping status and ETA for an order id like A123")
    OrderStatus getOrderStatus(@ToolParam(description = "Order id, e.g. A123") String orderId,
                               ToolContext ctx) {
        String userId = (String) ctx.getContext().get("userId");
        Order o = orders.findByIdAndCustomerId(orderId, userId)            // authorisation!
                .orElseThrow(() -> new IllegalArgumentException("Order " + orderId + " not found for this user"));
        return new OrderStatus(o.getId(), o.getStatus(), o.getEta());
    }

    @Tool(description = "List the user's most recent orders (max 5)")
    List<OrderSummary> recentOrders(ToolContext ctx) {
        return orders.findTop5ByCustomerIdOrderByCreatedAtDesc((String) ctx.getContext().get("userId"))
                .stream().map(OrderSummary::from).toList();
    }
}

record OrderStatus(String id, String status, LocalDate eta) {}
```

Use it in a request:

```java
String reply = chatClient.prompt()
    .system("You are ShopKart's support assistant. Use tools to look up real order data.")
    .user(userMessage)
    .tools(orderTools)                                         // register tool bean
    .toolContext(Map.of("userId", principal.getName()))        // trusted data, not shown to the model
    .call().content();
```

What happens: Spring AI sends the tool definitions, the model returns a tool call, Spring AI invokes `getOrderStatus("A123", ctx)`, serialises the record to JSON, sends it back, and returns the final text. Register tools for all requests with `.defaultTools(...)` on the builder.

### ToolContext: pass trusted data

`ToolContext` carries server-side data (user id, tenant, request id) to tools **without** putting it in the prompt. This is exactly the module 7/10 principle: authorisation uses authenticated identity, never model-supplied identity. The model can ask about order A999, but the repository query includes the user id, so it can't see other users' orders.

### Error handling

If a tool throws, Spring AI's default behaviour turns the exception message into the tool result so the model can recover ("Order A999 not found for this user"). Make exception messages actionable and free of secrets. You can customise this with a `ToolExecutionExceptionProcessor` (e.g. rethrow for certain exceptions).

### Return direct

Sometimes the tool result *is* the answer (e.g. a generated report link) and you don't want the model to rephrase it:

```java
@Tool(description = "Generate the invoice PDF link for an order", returnDirect = true)
String invoiceLink(String orderId, ToolContext ctx) { ... }
```

### Human approval for risky tools

Spring AI executes tools automatically, so put guardrails **inside** risky tools, or take control of execution. Pattern: the tool creates a *pending action* and returns a message; the UI asks the user to confirm; a separate endpoint executes it.

```java
@Tool(description = "Request a refund for an order. Creates a pending request the customer must confirm.")
String requestRefund(String orderId, String reason, ToolContext ctx) {
    String userId = (String) ctx.getContext().get("userId");
    Order o = orders.findByIdAndCustomerId(orderId, userId).orElseThrow();
    if (o.getTotal().compareTo(new BigDecimal("5000")) > 0) {
        return "Refunds above INR 5000 need a human agent; a ticket has been created.";
    }
    PendingAction p = pendingActions.create(userId, "REFUND", orderId, reason);
    return "Refund request " + p.id() + " created. Ask the customer to confirm it in the app.";
}
```

For full control, Spring AI supports **user-controlled tool execution**: disable internal execution (`internalToolExecutionEnabled(false)` in tool calling options), inspect the model's tool calls yourself, and run them via `ToolCallingManager` when approved. Useful for approval UIs and custom agent loops.

### Programmatic tools

Besides `@Tool`, you can define tools as functions (`FunctionToolCallback.builder(...)`) or expose existing `@Bean` functions, which is handy for dynamic tools defined at runtime.

### Observability

Spring AI emits Micrometer observations for chat calls and tool calls. With Actuator + an OTLP exporter (Zipkin, Jaeger, Grafana Tempo, Langfuse via OTel), you see each model call and tool invocation as spans, with token usage metrics, exactly the module 12 tracing ideas, wired into the Spring observability stack you already know.

```yaml
management:
  tracing:
    sampling:
      probability: 1.0
  observations:
    key-values:
      application: shopkart-ai
```

### Python vs Java

```python
# Python: you wrote ~40 lines of loop code (module 7)
```

```java
chatClient.prompt().user(msg).tools(orderTools).toolContext(ctx).call().content();
```

### Key takeaways
- Annotate bean methods with `@Tool`/`@ToolParam`; Spring AI generates schemas and runs the tool loop.
- Use `ToolContext` for trusted identity; enforce authorisation inside tools.
- Make errors actionable; use `returnDirect` when the tool output is the answer.
- For risky actions, create pending actions or take over execution for human approval; observe tool calls with Micrometer.
""", r"""
1. Implement `OrderTools` with JPA (H2 or MySQL) and 3 tools: status, recent orders, refund request (pending action).
2. Pass `userId` via `ToolContext` from Spring Security; write a test proving user B can't fetch user A's order even if the model asks.
3. Add a `POST /api/actions/{id}/confirm` endpoint that executes a pending refund.
4. Enable Actuator tracing and view the chat + tool spans in Zipkin (run it with Docker).
""", [
Q("What does Spring AI do with `@Tool` methods passed via `.tools(bean)`?", ["Nothing until you write the loop", "Generates tool schemas, sends them to the model, executes requested calls and returns results automatically", "Compiles them to Python", "Stores them in the vector DB"], 1, "Spring AI handles the whole tool-calling loop."),
Q("What is ToolContext used for?", ["Sending extra instructions to the model", "Passing trusted server-side data like the user id to tools without exposing it to the model", "Caching results", "Streaming tokens"], 1, "It keeps identity out of the prompt and available for authorisation."),
Q("How can you require human approval before a refund executes?", ["Ask nicely in the system prompt", "Have the tool create a pending action that a separate confirmed endpoint executes, or take over tool execution", "Set temperature to 0", "Use returnDirect"], 1, "Approval must be enforced in code, not by prompt."),
], [
R("Spring AI - Tool Calling", "https://docs.spring.io/spring-ai/reference/api/tools.html", "docs"),
R("Spring AI - Observability", "https://docs.spring.io/spring-ai/reference/observability/index.html", "docs"),
R("Spring Boot - Tracing (Micrometer)", "https://docs.spring.io/spring-boot/reference/actuator/tracing.html", "docs"),
]),

L("m13-mcp-spring", "MCP Servers and Clients with Spring AI", 40, r"""
## MCP meets Spring Boot

You learned MCP's architecture in module 10: hosts/clients connect to servers that expose tools, resources and prompts over stdio or Streamable HTTP. Spring AI provides Boot starters for both sides, built on the official MCP Java SDK. This is a very marketable skill: many companies want to expose their existing Spring services to AI assistants and agents, and you can do it with annotations.

### Exposing your Spring service as an MCP server

Dependency (WebMVC-based HTTP server; WebFlux and stdio variants also exist):

```xml
<dependency>
  <groupId>org.springframework.ai</groupId>
  <artifactId>spring-ai-starter-mcp-server-webmvc</artifactId>
</dependency>
```

```yaml
spring:
  ai:
    mcp:
      server:
        name: shopkart-orders
        version: 1.0.0
        protocol: STREAMABLE        # Streamable HTTP transport
```

Define tools with annotations. Recent Spring AI versions provide MCP-specific annotations:

```java
@Service
public class OrderMcpTools {

    private final OrderService orderService;
    public OrderMcpTools(OrderService s) { this.orderService = s; }

    @McpTool(description = "Get status and ETA for an order id like A123")
    public String getOrderStatus(
            @McpToolParam(description = "Order id", required = true) String orderId) {
        var o = orderService.findForCurrentClient(orderId);
        return o.map(x -> x.id() + ": " + x.status() + ", ETA " + x.eta())
                .orElse("Order " + orderId + " not found");
    }
}
```

In earlier 1.0-style setups, the same is done with Spring AI's `@Tool` methods registered through a `ToolCallbackProvider` bean:

```java
@Bean
ToolCallbackProvider orderTools(OrderTools tools) {
    return MethodToolCallbackProvider.builder().toolObjects(tools).build();
}
```

Check which style your Spring AI version documents; the concepts are identical. Resources and prompts can be exposed similarly (e.g. `@McpResource`, `@McpPrompt` in newer versions).

Run the app and connect any MCP host to `http://localhost:8080/mcp` (the default endpoint path may vary by version and is configurable). Test with the MCP Inspector (`npx @modelcontextprotocol/inspector`).

### Securing a remote MCP server

An MCP server is an API that AI agents call. Apply everything you know from Spring Security:
- Require authentication (OAuth 2.1 bearer tokens per the MCP authorization spec, or API keys for internal use) with `spring-boot-starter-oauth2-resource-server`.
- Authorise per tool and per resource; scope data to the calling user/tenant.
- Validate inputs, rate-limit, audit-log every call.
- Keep tools coarse-grained and read-only where possible; require explicit confirmation flows for writes.

### Consuming MCP servers from a Spring AI app (client)

```xml
<dependency>
  <groupId>org.springframework.ai</groupId>
  <artifactId>spring-ai-starter-mcp-client</artifactId>
</dependency>
```

```yaml
spring:
  ai:
    mcp:
      client:
        streamable-http:
          connections:
            orders:
              url: http://localhost:8080
        stdio:
          connections:
            filesystem:
              command: npx
              args: ["-y", "@modelcontextprotocol/server-filesystem", "/data/reports"]
```

The client starter connects to each server, discovers tools and exposes them as a `ToolCallbackProvider` bean, so the model can use them like local `@Tool` methods:

```java
@Bean
ChatClient agentClient(ChatClient.Builder builder, ToolCallbackProvider mcpTools) {
    return builder
        .defaultSystem("You are an operations assistant. Use tools to look up real data.")
        .defaultToolCallbacks(mcpTools)
        .build();
}

String answer = agentClient.prompt()
    .user("Which of today's delayed orders are over INR 10,000? Save a summary report.")
    .call().content();
```

Now your Spring app is an MCP **host**: one `ChatClient` can use tools from your own services, third-party MCP servers (GitHub, databases, filesystems) and other teams' servers, without custom integration code.

### Architecture pattern for enterprises

```
Existing Spring microservices (orders, payments, inventory)
   -> each exposes a small, secured MCP server (or one gateway server)
       -> consumed by: internal AI assistant (Spring AI host), IDE agents, Claude/ChatGPT enterprise connectors
```

This lets teams make their services "AI-accessible" once and reuse everywhere, just as they once exposed REST APIs.

### Key takeaways
- Spring AI has MCP server starters (WebMVC/WebFlux/stdio) and a client starter built on the MCP Java SDK.
- Expose tools with MCP annotations (or `@Tool` + `ToolCallbackProvider`), configure transport and name in YAML.
- Secure remote servers like any API: OAuth, per-tool authorisation, rate limits, audit logs.
- The client starter turns discovered MCP tools into `ToolCallbackProvider` beans for `ChatClient`.
""", r"""
1. Turn your `OrderService` into an MCP server with 2-3 tools using the Spring AI MCP server starter. Test with MCP Inspector.
2. Connect it to an MCP host (Claude Desktop/Claude Code, VS Code or Cursor) and ask questions about orders.
3. In a second Spring Boot app, use the MCP client starter to connect to your server plus the reference filesystem server, and build an assistant that answers questions and writes a report file.
4. Add API-key or OAuth resource-server protection to the MCP endpoint and confirm unauthenticated clients are rejected.
""", [
Q("What does the Spring AI MCP client starter expose to your application?", ["A JDBC DataSource", "A ToolCallbackProvider containing tools discovered from configured MCP servers", "A vector store", "A new LLM"], 1, "Discovered MCP tools become tool callbacks usable by ChatClient."),
Q("Which transport would a remote, shared MCP server built with Spring WebMVC typically use?", ["stdio", "Streamable HTTP", "FTP", "JMS"], 1, "Remote servers use HTTP-based transports; stdio is for local subprocesses."),
Q("Why expose existing Spring microservices as MCP servers?", ["To replace REST entirely", "So any MCP-capable AI host or agent can use them without custom integrations", "MCP is faster than SQL", "It removes the need for security"], 1, "MCP makes services reusable across AI clients, like REST did for apps."),
], [
R("Spring AI - MCP overview", "https://docs.spring.io/spring-ai/reference/api/mcp/mcp-overview.html", "docs"),
R("Spring AI - Getting started with MCP", "https://docs.spring.io/spring-ai/reference/guides/getting-started-mcp.html", "docs"),
R("MCP Java SDK (GitHub)", "https://github.com/modelcontextprotocol/java-sdk", "docs"),
R("MCP specification - Authorization", "https://modelcontextprotocol.io/specification/latest/basic/authorization", "docs"),
]),

L("m13-angular-integration", "Full Stack: Streaming AI Chat with Spring Boot and Angular", 50, r"""
## Putting your whole stack together

You already know Spring Boot + Angular + MySQL. Now add AI: a streaming chat UI in Angular, a Spring AI backend with memory, RAG and tools, JWT auth, and persistence. This lesson is the blueprint for your portfolio project, the kind of thing product companies want to see from a "Java + AI" engineer.

### Backend: a streaming chat endpoint

```java
public record ChatRequest(String conversationId, String message) {}

@RestController
@RequestMapping("/api/chat")
class ChatController {

    private final ChatClient chatClient;

    ChatController(ChatClient.Builder builder, ChatMemory memory, VectorStore store, OrderTools tools) {
        this.chatClient = builder
            .defaultSystem("You are ShopKart's assistant. Answer from documents and tools; say when you don't know.")
            .defaultAdvisors(MessageChatMemoryAdvisor.builder(memory).build(),
                             QuestionAnswerAdvisor.builder(store).build())
            .defaultTools(tools)
            .build();
    }

    @PostMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    Flux<ServerSentEvent<String>> stream(@RequestBody ChatRequest req, Principal principal) {
        String convId = principal.getName() + ":" + req.conversationId();   // scope memory per user
        return chatClient.prompt()
            .user(req.message())
            .advisors(a -> a.param(ChatMemory.CONVERSATION_ID, convId)
                            .param(QuestionAnswerAdvisor.FILTER_EXPRESSION,
                                   "tenantId == '" + tenantOf(principal) + "'"))
            .toolContext(Map.of("userId", principal.getName()))
            .stream().content()
            .map(token -> ServerSentEvent.builder(token).build())
            .concatWith(Flux.just(ServerSentEvent.<String>builder("[DONE]").event("done").build()))
            .onErrorResume(e -> Flux.just(ServerSentEvent.<String>builder("Sorry, something went wrong.")
                                          .event("error").build()));
    }
}
```

Notes:
- Memory id includes the authenticated user, so users can't read each other's conversations by guessing ids.
- Wrapping tokens in `ServerSentEvent` lets you send named events (`done`, `error`) and keeps whitespace intact.
- With Spring MVC, returning `Flux` works when Reactor is on the classpath; with virtual threads (Java 21) or WebFlux you scale to many concurrent slow streams.

### Frontend: reading a POST SSE stream in Angular

`EventSource` only supports GET without custom headers, but we need POST + JWT. Use `fetch` with a stream reader wrapped in an RxJS `Observable`:

```typescript
// chat.service.ts
@Injectable({ providedIn: 'root' })
export class ChatService {
  private auth = inject(AuthService);

  stream(conversationId: string, message: string): Observable<string> {
    return new Observable<string>(subscriber => {
      const controller = new AbortController();
      fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json',
                   'Authorization': `Bearer ${this.auth.token()}` },
        body: JSON.stringify({ conversationId, message }),
        signal: controller.signal,
      }).then(async res => {
        if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
        const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
        let buffer = '';
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += value;
          const events = buffer.split('\n\n');
          buffer = events.pop() ?? '';
          for (const evt of events) {
            const isDone = evt.includes('event:done');
            const data = evt.split('\n').filter(l => l.startsWith('data:'))
                            .map(l => l.slice(5)).join('\n');
            if (isDone) { subscriber.complete(); return; }
            subscriber.next(data);
          }
        }
        subscriber.complete();
      }).catch(err => subscriber.error(err));
      return () => controller.abort();          // unsubscribe cancels the request (saves tokens)
    });
  }
}
```

(Libraries like `@microsoft/fetch-event-source` handle SSE parsing edge cases if you prefer.)

### Frontend: component with signals

```typescript
@Component({
  selector: 'app-chat',
  template: `
    @for (m of messages(); track $index) {
      <div [class]="m.role"><div [innerHTML]="m.text | markdown"></div></div>
    }
    <form (submit)="send(); $event.preventDefault()">
      <input [(ngModel)]="draft" name="draft" [disabled]="streaming()" />
      <button [disabled]="streaming()">Send</button>
      @if (streaming()) { <button type="button" (click)="stop()">Stop</button> }
    </form>`,
  imports: [FormsModule, MarkdownPipe],
})
export class ChatComponent {
  private chat = inject(ChatService);
  messages = signal<{ role: 'user' | 'assistant'; text: string }[]>([]);
  streaming = signal(false);
  draft = '';
  private sub?: Subscription;
  private conversationId = crypto.randomUUID();

  send() {
    const text = this.draft.trim();
    if (!text) return;
    this.draft = '';
    this.messages.update(m => [...m, { role: 'user', text }, { role: 'assistant', text: '' }]);
    this.streaming.set(true);
    this.sub = this.chat.stream(this.conversationId, text).subscribe({
      next: tok => this.messages.update(m => {
        const copy = [...m];
        copy[copy.length - 1] = { ...copy[copy.length - 1], text: copy[copy.length - 1].text + tok };
        return copy;
      }),
      complete: () => this.streaming.set(false),
      error: () => this.streaming.set(false),
    });
  }
  stop() { this.sub?.unsubscribe(); this.streaming.set(false); }
}
```

Render Markdown **sanitised** (Angular's `[innerHTML]` sanitises by default; keep it that way). Never bypass sanitisation for model output (module 12: XSS/exfiltration).

### Production checklist for the full stack

- **Auth**: JWT required on `/api/chat/**`; tenant and user from the token.
- **Rate limits** per user (Bucket4j or gateway) and max message length.
- **Persistence**: JDBC chat memory in MySQL/Postgres; store conversations for the "history" sidebar; feedback table (thumbs up/down linked to a message id).
- **Observability**: Actuator + Micrometer tracing; log tokens and cost per conversation.
- **Resilience**: timeouts, retry config (`spring.ai.retry.*`), fallback model, user-friendly error events.
- **Proxy config**: disable response buffering for SSE in Nginx (`proxy_buffering off`).
- **Evals in CI**: JUnit eval suite gating releases (lessons 2 and 4).

### Key takeaways
- Spring AI streams `Flux<String>`; wrap in `ServerSentEvent` with done/error events, scoped per user.
- Angular consumes POST SSE via `fetch` + stream reader inside an `Observable`; unsubscribe aborts the request.
- Signals make incremental rendering simple; always sanitise model output.
- Add auth, rate limits, persistence, observability and evals to make it production-ready.
""", r"""
1. Implement the streaming chat backend with memory, RAG and tools, protected by JWT.
2. Build the Angular chat component with streaming, a Stop button and sanitised Markdown rendering.
3. Persist conversations and add a history sidebar plus thumbs up/down feedback stored per message.
4. Load test with 20 concurrent streaming users (k6 or Gatling) and record p95 TTFT; try enabling virtual threads (`spring.threads.virtual.enabled=true`).
""", [
Q("Why use fetch + a stream reader instead of EventSource in this Angular client?", ["EventSource is deprecated", "EventSource only supports GET without custom headers, but we need POST with a JWT", "fetch is faster for JSON", "Angular forbids EventSource"], 1, "fetch allows POST bodies and Authorization headers while streaming."),
Q("Why include the authenticated user in the chat memory conversation id?", ["To shorten prompts", "So users can't access other users' conversation history by guessing ids", "It's required by SSE", "To improve model quality"], 1, "Server-side scoping enforces isolation."),
Q("What should happen when the user clicks Stop?", ["Nothing", "Unsubscribe, which aborts the fetch so the backend stops generating and you stop paying for tokens", "Reload the page", "Clear the database"], 1, "Cancelling upstream saves cost and resources."),
], [
R("Spring AI - ChatClient streaming", "https://docs.spring.io/spring-ai/reference/api/chatclient.html", "docs"),
R("MDN - Streams API (ReadableStream)", "https://developer.mozilla.org/en-US/docs/Web/API/Streams_API/Using_readable_streams", "docs"),
R("Angular - Signals guide", "https://angular.dev/guide/signals", "docs"),
R("Josh Long - Spring Tips videos on Spring AI (YouTube)", "https://www.youtube.com/@SpringSourceDev", "video"),
]),
]

for _l in lessons:
    _l["content"] = _l["content"].replace("<<TQ>>", '"' * 3)

MODULE = M(
    "m13-spring-ai", 13, "AI in Java with Spring AI", "Advanced", 2,
    "Bring everything you learned in Python into your existing Java stack with Spring AI: ChatClient, structured output, embeddings with PgVector, RAG advisors, tool calling and MCP. Finish with a full-stack streaming AI chat in Spring Boot and Angular, the profile that sets a Java developer apart as an AI engineer.",
    [
        "Build Spring Boot services with ChatClient, prompt templates, memory and streaming",
        "Map LLM output to Java records with validation",
        "Implement document ingestion and RAG with PgVectorStore and advisors",
        "Expose secure @Tool methods and MCP servers/clients from Spring",
        "Ship a full-stack streaming AI chat with Angular, JWT auth and observability",
    ],
    lessons,
    ("ShopKart AI Assistant: Spring Boot + Angular + Spring AI", r"""
Build a production-style, full-stack AI assistant on your home stack:

1. **Backend (Spring Boot + Spring AI)**: JWT auth, `ChatClient` with JDBC chat memory, RAG over policy/FAQ documents in PgVector (ingestion endpoint with Tika + TokenTextSplitter), tenant filters from the security context.
2. **Tools**: `@Tool` methods over JPA order data (status, recent orders, refund request as a pending action with a confirm endpoint) using `ToolContext` for the user id.
3. **MCP**: expose the order tools as a secured MCP server, and demo it from Claude Desktop/VS Code.
4. **Frontend (Angular, signals)**: streaming chat over POST SSE, stop button, sanitised Markdown, sources display, conversation history and feedback buttons.
5. **Quality and ops**: JUnit eval suite (30+ cases) with an LLM judge, Micrometer tracing to Zipkin, token/cost logging, Docker Compose (app + Postgres/pgvector + Zipkin).

**Deliverable:** GitHub repo, README with architecture diagram, screenshots/GIF, eval results and "how I'd scale this" section. Put this at the top of your resume as your Java + AI flagship project.
"""),
)
