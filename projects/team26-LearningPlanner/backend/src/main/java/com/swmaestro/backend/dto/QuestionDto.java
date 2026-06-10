package com.swmaestro.backend.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public class QuestionDto {

    private String id;
    private String label;
    private String type;
    private String placeholder;
    private Boolean required;
    private String defaultValue;
    private List<OptionDto> options;

    public QuestionDto() {}

    public QuestionDto(String id, String label, String type, String placeholder,
                       Boolean required, String defaultValue, List<OptionDto> options) {
        this.id           = id;
        this.label        = label;
        this.type         = type;
        this.placeholder  = placeholder;
        this.required     = required;
        this.defaultValue = defaultValue;
        this.options      = options;
    }

    public String getId()           { return id; }
    public String getLabel()        { return label; }
    public String getType()         { return type; }
    public String getPlaceholder()  { return placeholder; }
    public Boolean getRequired()    { return required; }
    public String getDefaultValue() { return defaultValue; }
    public List<OptionDto> getOptions() { return options; }

    public void setId(String id)                    { this.id = id; }
    public void setLabel(String label)              { this.label = label; }
    public void setType(String type)                { this.type = type; }
    public void setPlaceholder(String placeholder)  { this.placeholder = placeholder; }
    public void setRequired(Boolean required)       { this.required = required; }
    public void setDefaultValue(String defaultValue){ this.defaultValue = defaultValue; }
    public void setOptions(List<OptionDto> options) { this.options = options; }
}
