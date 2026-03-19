# Host ↔ Participant Relationship

## 1. Control Model

The system follows a **centralized orchestration model**:

* **Host (runner + decision)**

  * controls *session lifecycle*
  * selects *who speaks*
  * defines *structure (subtopics, turns)*
  * produces *global summaries (conclusion, synthesis)*

* **Participants (agents)**

  * produce *localized contributions*
  * maintain *individual evolving state*
  * do **not** control flow or termination

Formally:

```
Host = global state transition function
Agent = local state transformer
```

---

## 2. Responsibility Separation

### Host responsibilities

1. **Session management**

   * initialize `ConversationState`
   * manage lifecycle: start → subtopics → end

2. **Subtopic management**

   * create subtopics (`generate_subtopics`)
   * maintain:

     * `current_subtopic_index`
     * `status ∈ {PENDING, ONGOING, FINISH}`
   * enforce progression

3. **Turn scheduling**

   * select next speaker (`select_next_speaker`)
   * enforce stopping conditions:

     * no speaker
     * max turns

4. **Global summarization**

   * subtopic-level:

     * `generate_subtopic_conclusion`
   * session-level:

     * `generate_final_synthesis`

---

### Participant responsibilities

1. **Reply generation**

   * conditioned on:

     * role
     * traits
     * goals
     * summary_text
     * conversation history

2. **State compression**

   * update:

     * `summary_text`
     * `latest_open_questions`
     * `current_focus`

3. **Local continuity**

   * ensure next reply is consistent with prior contributions

---

## 3. State Hierarchy

The system operates on three nested layers:

### (1) Session level

* global objective: `state.achievement`
* final output: synthesis

### (2) Subtopic level

* unit of structured discussion

* fields:

  * `title`
  * `achievement`
  * `conclusion`
  * `status`

* lifecycle:

```
PENDING → ONGOING → FINISH
```

### (3) Turn level

* atomic interaction unit
* each turn:

  * one speaker
  * one message
* produces:

  * updated agent runtime
  * snapshot for all participants

---

## 4. Data Flow

### Forward flow (generation)

```
state → decision → select speaker
      → generation → reply
      → generation → summary update
      → state update
```

### Backward compression (memory)

```
turn history → summary_text
             → reduced context for next turn
```

### Subtopic closure

```
subtopic turns → host LLM → conclusion
               → stored in SubtopicPlan
```

---

## 5. Key Design Properties

### 1. Deterministic structure, probabilistic content

* flow is fixed (runner)
* content is LLM-generated

### 2. Bounded context growth

* summaries replace long history
* prevents token explosion

### 3. Clear separation of concerns

* runner = orchestration
* decision = host intelligence
* generation = agent behavior

### 4. Hierarchical memory

* turn → summary → subtopic → synthesis

---

If you want to extend this further, the next structural improvement would be:

* introducing **explicit turn-phase states** (DECIDING / GENERATING / SUMMARIZING)
* or adding **interrupt / re-plan subtopic capability** when progress stagnates

Both integrate naturally with the current architecture.


``` mermaid
flowchart TB
    H[Host / Orchestrator]

    subgraph SessionState[ConversationState]
        CS1[Topic / Achievement]
        CS2[Subtopics]
        CS3[Turns]
        CS4[Participant Runtime States]
        CS5[Snapshots]
    end

    subgraph Participants
        P1[Agent A]
        P2[Agent B]
        P3[Agent C]
        P4[Agent N]
    end

    H --> SessionState
    SessionState --> H

    H -->|select speaker| P1
    H -->|select speaker| P2
    H -->|select speaker| P3
    H -->|select speaker| P4

    P1 -->|reply / summary| H
    P2 -->|reply / summary| H
    P3 -->|reply / summary| H
    P4 -->|reply / summary| H
```

