package com.swmaestro.backend.dto;

import com.fasterxml.jackson.annotation.JsonAnySetter;
import com.fasterxml.jackson.annotation.JsonIgnore;

import java.util.HashMap;
import java.util.Map;

public class BuildRequest {

    private String studyTarget;
    private String level;
    private int studyWeeks;

    @JsonIgnore
    private Map<String, String> answers = new HashMap<>();

    @JsonAnySetter
    public void addAnswer(String key, Object value) {
        answers.put(key, value != null ? value.toString() : null);
    }

    public String getStudyTarget()       { return studyTarget; }
    public String getLevel()             { return level; }
    public int getStudyWeeks()           { return studyWeeks; }
    public Map<String, String> getAnswers() { return answers; }

    public void setStudyTarget(String studyTarget) { this.studyTarget = studyTarget; }
    public void setLevel(String level)             { this.level = level; }
    public void setStudyWeeks(int studyWeeks)      { this.studyWeeks = studyWeeks; }
}
