``` mermaid
stateDiagram-v2
    [*] --> Idle

    Idle --> Selected : selected by host

    Selected --> LoadRuntimeState
    LoadRuntimeState --> BuildReplyPrompt
    BuildReplyPrompt --> GenerateReply

    GenerateReply --> ReplyAccepted : valid JSON
    GenerateReply --> ReplyFallback : invalid / empty

    ReplyAccepted --> AppendReplyTurn
    ReplyFallback --> AppendReplyTurn

    AppendReplyTurn --> UpdateReplyRuntime

    UpdateReplyRuntime --> BuildSummaryPrompt
    BuildSummaryPrompt --> GenerateSummary
    GenerateSummary --> UpdateSummaryRuntime

    UpdateSummaryRuntime --> PersistSnapshot
    PersistSnapshot --> Waiting
    Waiting --> [*]

    state UpdateReplyRuntime {
        [*] --> SetLatestReply
        SetLatestReply --> IncrementTimesSpoken
        IncrementTimesSpoken --> UpdateLastSpokenTurnIndex
        UpdateLastSpokenTurnIndex --> [*]
    }

    state UpdateSummaryRuntime {
        [*] --> RefreshSummaryText
        RefreshSummaryText --> RefreshOpenQuestions
        RefreshOpenQuestions --> RefreshCurrentFocus
        RefreshCurrentFocus --> [*]
    }
```