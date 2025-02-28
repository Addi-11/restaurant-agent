# Restaurant Agent Assignment
## Goal
Build an intelligent restaurant assistant that can handle multi-turn conversations, process user queries, and interact with external tools (e.g., restaurant databases, reservation systems) to provide real-time information.

## Use case
Virtual concierge for FoodieSpot, helping customers find restaurants, check availability, fetch menus, and make reservations via a conversational interface. A user can interact through chat, ask about restaurants near them, browse menus, and book a table—all in a single, natural conversation flow. The agent will integrate with a restaurant database, maintain user preferences, and ensure real-time updates

### State Transition Diagram

![alt text](images/agent-flow.png)

### Key Steps (agent flow)

1. User initiates conversation ("What’s on the menu at Blue Tokai?")
2. Intent detection & classification
3. Agent calls the appropriate service (e.g., FetchMenuService)
4. Agent responds with relevant information, fetching information from the knowledge base.
5. User asks a follow-up question (multi-turn handled, e.g., "Do they have vegan options?")
6. Agent maintains context & continues conversation
7. If reservation needed, agent transitions to booking flow
8. Booking confirmation & conversation closure

### Thought Process for Foodie Spot Agent 

1. **Intent Classification:** LLM determines intent of user message(e.g., `reserve_restaurant`, `fetch_price`, `search_restaurant`).  

6. **Prompt Routing & Parallelization:** Routes queries correctly based on intent.

2. **Events Creation:**  Logs events like `intent_identified`, `tool_called`, `response_generated` for tracking.  

3. **Response Format for Function Calling:** LLM outputs structured JSON with function name and parameters.  

4. **Function Calling & Knowledge Base Lookup:** Calls appropriate tool (e.g., `fetch_price` tool) to retrieve structured data.  

5. **Knowledge Base Search & Retrieval:** Searches and extracts exact or relaxed matches in restaurant data (menu, pricing, location).  

6. **Final Response Generation:** LLM generates the final response using the information from the function and chat context.

8. **TODO: Confirmation Generation:** Asks for user confirmation before final actions (e.g., booking a table).

## Agent Features

- Natural Language Processing for intent detection
- Tool calling ability for real-time menu fetch, availability checks, and reservations
- Multi-turn conversation support
- Context retention across turns

#### Knowledge Bases (KBs) required

- Restaurant Menus
- Location & Availability Data
- Reservation System

#### Tools required

- Fetch menu
- Check table availability
- Make a reservation

#### Future Scope

- Pluggable model support
- Handle vague user queries (e.g., "I need something spicy near me")
- Support voice input in later versions
- Personalization based on past interactions
- Other language integration
- SQL knowledge base for tool calling

#### Future Required Integrations
- Restaurant Database APIs (Menus, Reservations, Availability)
- CRM System (for user preferences & personalization)
- Payment Gateway (future expansion)

### Long Term Goal
Fully automated conversational agent.

### Success Criteria
- High accuracy in intent detection (above 90%)
- Seamless tool integration for fetching menus, checking availability, and booking tables
- Multi-turn context retention for better user experience
- Minimal user corrections (spelling errors, vague queries should still work well)

### Scale up / Rollout Strategy

### Key Future Challenges

- Handling ambiguous user queries (e.g., "Is it busy tonight?")
- Understanding misspellings & variations of restaurant names
- Optimizing API calls to prevent latency issues

## Current Agent Limitations
- Spelling mistakes not tolerated for query searches
- Restaurant names must be exact, including "The" or numbers (e.g., "The Grill House" is different from "Grill House")
- Context retention limited to short-term memory (improving over time with training)
- Each query takes some time to process by the model.
- Text generation model has limitation with token generated, or detecing <EOS>. Instruction tuned model for chat will give better results. Current Agent requires a lot of regex filtering of the model output.
- Powerful model can classify the query intent, and the search intent with much more accuracy.
- Recommendation criteria is woozy,
- Data model limitations, need sql for better query generation, right now json doesnt look elegant
