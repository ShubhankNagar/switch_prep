package com.switchprep;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles({"dev", "test"})
class ApiFlowTest {

    @Autowired
    MockMvc mvc;

    @Autowired
    ObjectMapper json;

    private String register(String username) throws Exception {
        String body = mvc.perform(post("/api/auth/register").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"username\":\"" + username + "\",\"password\":\"secret123\",\"displayName\":\"Raj\"}"))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();
        JsonNode node = json.readTree(body);
        return node.get("token").asText();
    }

    @Test
    void protectedEndpointsNeedToken() throws Exception {
        mvc.perform(get("/api/progress")).andExpect(status().isUnauthorized());
    }

    @Test
    void registerLoginAndTrackProgress() throws Exception {
        String token = register("raj");

        mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"username\":\"raj\",\"password\":\"secret123\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.user.displayName").value("Raj"));

        mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"username\":\"raj\",\"password\":\"wrong-pass\"}"))
                .andExpect(status().isUnauthorized());

        mvc.perform(put("/api/progress/dsa:two-sum").header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"section\":\"dsa\",\"done\":true,\"note\":\"hash map\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.done").value(true));

        mvc.perform(put("/api/progress/dsa:two-sum").header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"section\":\"dsa\",\"revise\":true}"))
                .andExpect(jsonPath("$.done").value(true))
                .andExpect(jsonPath("$.revise").value(true))
                .andExpect(jsonPath("$.note").value("hash map"));

        mvc.perform(post("/api/quiz-attempts").header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"quizKey\":\"final:d1\",\"score\":15,\"total\":20}"))
                .andExpect(status().isCreated());

        mvc.perform(get("/api/progress").header("Authorization", "Bearer " + token))
                .andExpect(jsonPath("$.length()").value(1));

        mvc.perform(get("/api/stats").header("Authorization", "Bearer " + token))
                .andExpect(jsonPath("$.totalDone").value(1))
                .andExpect(jsonPath("$.doneBySection.dsa").value(1))
                .andExpect(jsonPath("$.currentStreak").value(1));
    }

    @Test
    void duplicateUsernameIsRejected() throws Exception {
        register("dup-user");
        mvc.perform(post("/api/auth/register").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"username\":\"dup-user\",\"password\":\"secret123\"}"))
                .andExpect(status().isConflict());
    }

    @Test
    void habitsAndDailyLogs() throws Exception {
        String token = register("habit-user");

        mvc.perform(get("/api/habits").header("Authorization", "Bearer " + token))
                .andExpect(status().isNoContent());

        mvc.perform(put("/api/habits").header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"habitsJson\":\"[{\\\"id\\\":\\\"dsa\\\",\\\"target\\\":2}]\"}"))
                .andExpect(status().isOk());

        mvc.perform(get("/api/habits").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.habitsJson").value("[{\"id\":\"dsa\",\"target\":2}]"));

        mvc.perform(put("/api/habit-logs/2026-10-09").header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"valuesJson\":\"{\\\"apply\\\":5}\",\"minutes\":90,\"journal\":\"Learned outbox\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.minutes").value(90));

        // partial update keeps other fields
        mvc.perform(put("/api/habit-logs/2026-10-09").header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"minutes\":120}"))
                .andExpect(jsonPath("$.minutes").value(120))
                .andExpect(jsonPath("$.journal").value("Learned outbox"));

        mvc.perform(get("/api/habit-logs?from=2026-10-01&to=2026-10-31").header("Authorization", "Bearer " + token))
                .andExpect(jsonPath("$.length()").value(1))
                .andExpect(jsonPath("$[0].date").value("2026-10-09"));

        mvc.perform(put("/api/habit-logs/2026-10-09").header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"minutes\":5000}"))
                .andExpect(status().isBadRequest());
    }
}
