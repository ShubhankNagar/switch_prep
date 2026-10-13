package com.switchprep;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

/** The switches and per-user caps a public deployment relies on, with the caps set low enough to hit. */
@SpringBootTest(properties = {
        "spring.datasource.url=jdbc:h2:mem:switchprep-rules;MODE=MySQL;DATABASE_TO_LOWER=TRUE;DB_CLOSE_DELAY=-1",
        "app.auth.password-login=false",
        "app.limits.max-progress-items=2",
        "app.limits.max-note-chars-total=30",
        "app.limits.max-quiz-attempts=1",
        "app.limits.max-request-bytes=1000",
})
@AutoConfigureMockMvc
@ActiveProfiles({"dev", "test"})
@Import(FakeGoogleConfig.class)
class PublicDeploymentRulesTest {

    @Autowired
    MockMvc mvc;

    @Autowired
    ObjectMapper json;

    private String signIn(String sub) throws Exception {
        String body = mvc.perform(post("/api/auth/google").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"credential\":\"google:" + sub + ":" + sub + "@example.com:User\"}"))
                .andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString();
        return "Bearer " + json.readTree(body).get("token").asText();
    }

    private org.springframework.test.web.servlet.ResultActions tick(String auth, String key, String body) throws Exception {
        return mvc.perform(put("/api/progress/" + key).header("Authorization", auth)
                .contentType(MediaType.APPLICATION_JSON).content(body));
    }

    @Test
    void passwordAccountsAreSwitchedOff() throws Exception {
        mvc.perform(post("/api/auth/register").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"username\":\"someone\",\"password\":\"secret123\"}"))
                .andExpect(status().isForbidden());
        mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"username\":\"someone\",\"password\":\"secret123\"}"))
                .andExpect(status().isForbidden());
    }

    @Test
    void trackedItemsAreCappedPerAccount() throws Exception {
        String auth = signIn("cap-items");
        tick(auth, "dsa:a", "{\"section\":\"dsa\",\"done\":true}").andExpect(status().isOk());
        tick(auth, "dsa:b", "{\"section\":\"dsa\",\"done\":true}").andExpect(status().isOk());
        tick(auth, "dsa:c", "{\"section\":\"dsa\",\"done\":true}").andExpect(status().isUnprocessableEntity());
        // existing items can still be changed, and another account is unaffected
        tick(auth, "dsa:a", "{\"section\":\"dsa\",\"done\":false}").andExpect(status().isOk());
        tick(signIn("cap-items-other"), "dsa:c", "{\"section\":\"dsa\",\"done\":true}").andExpect(status().isOk());

        mvc.perform(post("/api/progress/import").header("Authorization", auth).contentType(MediaType.APPLICATION_JSON)
                        .content("[{\"key\":\"dsa:d\",\"section\":\"dsa\",\"done\":true,\"revise\":false}]"))
                .andExpect(status().isUnprocessableEntity());
        mvc.perform(get("/api/progress").header("Authorization", auth)).andExpect(jsonPath("$.length()").value(2));
    }

    @Test
    void notesAreCappedPerAccount() throws Exception {
        String auth = signIn("cap-notes");
        tick(auth, "dsa:a", "{\"section\":\"dsa\",\"note\":\"twenty characters ok\"}").andExpect(status().isOk());
        tick(auth, "dsa:b", "{\"section\":\"dsa\",\"note\":\"this one goes over the cap\"}")
                .andExpect(status().isUnprocessableEntity());
        // the rejected note was not stored
        mvc.perform(get("/api/progress").header("Authorization", auth)).andExpect(jsonPath("$.length()").value(1));
    }

    @Test
    void quizAttemptsAreCappedPerAccount() throws Exception {
        String auth = signIn("cap-quiz");
        String attempt = "{\"quizKey\":\"final:d1\",\"score\":1,\"total\":2}";
        mvc.perform(post("/api/quiz-attempts").header("Authorization", auth).contentType(MediaType.APPLICATION_JSON)
                .content(attempt)).andExpect(status().isCreated());
        mvc.perform(post("/api/quiz-attempts").header("Authorization", auth).contentType(MediaType.APPLICATION_JSON)
                .content(attempt)).andExpect(status().isUnprocessableEntity());
    }

    @Test
    void oversizedRequestsAreRefused() throws Exception {
        String auth = signIn("cap-size");
        tick(auth, "dsa:a", "{\"section\":\"dsa\",\"note\":\"" + "x".repeat(2000) + "\"}")
                .andExpect(status().isPayloadTooLarge());
    }

    @Test
    void overlongKeysAreRefused() throws Exception {
        tick(signIn("cap-key"), "k".repeat(151), "{\"section\":\"dsa\",\"done\":true}").andExpect(status().isBadRequest());
    }

    @Test
    void healthStaysPublic() throws Exception {
        mvc.perform(get("/actuator/health")).andExpect(status().isOk());
        mvc.perform(get("/actuator/health/liveness")).andExpect(status().isOk());
    }
}
