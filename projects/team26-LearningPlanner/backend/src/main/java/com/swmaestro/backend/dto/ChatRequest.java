package com.swmaestro.backend.dto;

import java.util.List;

public record ChatRequest(String message, String curriculum, List<String> editHistory) {

    public List<String> editHistory() {
        return editHistory != null ? editHistory : List.of();
    }
}
