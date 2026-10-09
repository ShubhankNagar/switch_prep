package com.switchprep.progress;

import com.switchprep.auth.CurrentUser;
import com.switchprep.progress.ProgressDtos.ProgressItem;
import com.switchprep.progress.ProgressDtos.ProgressUpdate;
import jakarta.validation.Valid;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/progress")
public class ProgressController {

    private final ProgressService service;
    private final CurrentUser currentUser;

    public ProgressController(ProgressService service, CurrentUser currentUser) {
        this.service = service;
        this.currentUser = currentUser;
    }

    @GetMapping
    public List<ProgressItem> list() {
        return service.list(currentUser.id());
    }

    @PutMapping("/{key}")
    public ProgressItem upsert(@PathVariable String key, @Valid @RequestBody ProgressUpdate update) {
        return service.upsert(currentUser.id(), key, update);
    }

    @DeleteMapping("/{key}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable String key) {
        service.delete(currentUser.id(), key);
    }

    @PostMapping("/import")
    public Map<String, Integer> importItems(@RequestBody List<ProgressItem> items) {
        return Map.of("imported", service.importItems(currentUser.id(), items));
    }

    @DeleteMapping
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void reset() {
        service.reset(currentUser.id());
    }
}
