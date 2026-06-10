package com.swmaestro.backend.controller;

import com.swmaestro.backend.dto.*;
import com.swmaestro.backend.service.CurriculumService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api")
public class CurriculumController {

    private final CurriculumService curriculumService;

    public CurriculumController(CurriculumService curriculumService) {
        this.curriculumService = curriculumService;
    }

    @PostMapping("/generate")
    public ResponseEntity<GenerateResponse> generate(@RequestBody GenerateRequest req) {
        return ResponseEntity.ok(curriculumService.generateQuestions(req));
    }

    @PostMapping("/build")
    public ResponseEntity<BuildResponse> build(@RequestBody BuildRequest req) {
        return ResponseEntity.ok(curriculumService.buildCurriculum(req));
    }

    @PostMapping("/chat")
    public ResponseEntity<ChatResponse> chat(@RequestBody ChatRequest req) {
        return ResponseEntity.ok(curriculumService.chat(req));
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Map<String, String>> handleValidation(IllegalArgumentException e) {
        return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, String>> handleGeneral(Exception e) {
        return ResponseEntity.internalServerError().body(Map.of("error", e.getMessage()));
    }
}
