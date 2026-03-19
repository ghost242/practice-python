``` mermaid
flowchart TD
    A[Start Session] --> B[Initialize ConversationState]
    B --> C[Register Participants + RuntimeState]
    C --> D[Generate Subtopics via decision module]

    D --> E[Set current_subtopic_index = 0]
    E --> F[Mark subtopic ONGOING]
    F --> G[Append SUBTOPIC kickoff turn]
    G --> H[Record initial snapshots]

    H --> I{Turn Loop}

    I --> J[Select next speaker via decision]
    J --> K{Speaker exists?}

    K -- Yes --> L[Trigger agent workflow]
    L --> M[Append reply turn]
    M --> N[Update agent runtime]
    N --> O[Update agent summary]
    O --> P[Record snapshots]
    P --> Q{Turn limit reached?}

    Q -- No --> I
    Q -- Yes --> R[Close subtopic]

    K -- No --> R

    R --> S[Collect subtopic turns]
    S --> T[Generate subtopic conclusion via decision]
    T --> U[Append SUBTOPIC CONCLUSION turn]
    U --> V[Persist SubtopicPlan.conclusion]

    V --> W{More subtopics?}

    W -- Yes --> X[Advance current_subtopic_index]
    X --> F

    W -- No --> Y[Generate final synthesis]
    Y --> Z[Append SYNTHESIS turn]
    Z --> End[End Session]
```