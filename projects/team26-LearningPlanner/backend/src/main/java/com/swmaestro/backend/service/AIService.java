package com.swmaestro.backend.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.http.converter.StringHttpMessageConverter;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;

@Service
public class AIService {

    private static final String API_URL = "https://api.upstage.ai/v1/chat/completions";
    private static final String MODEL   = "solar-pro";

    @Value("${upstage.api-key}")
    private String apiKey;

    private final RestTemplate restTemplate;

    public AIService() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5_000);
        factory.setReadTimeout(60_000);
        restTemplate = new RestTemplate(factory);
        restTemplate.getMessageConverters()
            .forEach(c -> {
                if (c instanceof StringHttpMessageConverter sc) {
                    sc.setDefaultCharset(StandardCharsets.UTF_8);
                }
            });
    }

    public String call(String prompt) {
        String result = requestChat(prompt);
        return sanitize(result);
    }

    private String requestChat(String prompt) {
        Map<String, Object> body = Map.of(
            "model", MODEL,
            "messages", List.of(
                Map.of("role", "system", "content", "You must always respond in Korean (한국어) only. Never use Chinese characters (漢字) or Chinese language. Use only Korean Hangul."),
                Map.of("role", "user", "content", prompt)
            )
        );

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.setBearerAuth(apiKey);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);

        Map<?, ?> response = restTemplate.postForObject(API_URL, entity, Map.class);
        List<?> choices = (List<?>) response.get("choices");
        Map<?, ?> message = (Map<?, ?>) ((Map<?, ?>) choices.get(0)).get("message");
        return (String) message.get("content");
    }

    private String sanitize(String text) {
        text = text.replaceAll("[^\\u0000-\\u024F\\u2000-\\u206F\\u2190-\\u2BFF" +
                               "\\u1100-\\u11FF\\u3130-\\u318F\\uAC00-\\uD7A3" +
                               "\\uD7B0-\\uD7FF\\n\\r\\t]", "")
                   .replaceAll("[ \\t]{2,}", " ")
                   .trim();
        text = text.replaceAll("\\|[ \\t]+\\|", "|\n|");
        return text;
    }

    public String extractJson(String text) {
        text = text.trim();
        if (text.startsWith("```")) {
            text = text.replaceAll("(?s)^```[a-z]*\\s*", "").replaceAll("```\\s*$", "").trim();
        }
        return text;
    }
}
