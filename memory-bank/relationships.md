# Freya Backend: Table Relationships & Constraints

## 1. User
- **Primary Key:** `id`
- **Relationships:**
  - One-to-many with `Conversation` (`user_id` in Conversation)
  - One-to-many with `UserFact` (`user_id` in UserFact)
  - One-to-many with `Message` (`user_id` in Message; sender)

## 2. Conversation
- **Primary Key:** `id`
- **Foreign Key:** `user_id` references `User(id)`
- **Relationships:**
  - Many-to-one with `User`
  - One-to-many with `Message` (`conversation_id` in Message)

## 3. Message
- **Primary Key:** `id`
- **Foreign Keys:**
  - `conversation_id` references `Conversation(id)`
  - `user_id` references `User(id)`
- **Relationships:**
  - Many-to-one with `Conversation`
  - Many-to-one with `User` (sender)
  - Many-to-many with `Topic` (via `MessageTopic`)

## 4. UserFact
- **Primary Key:** `id`
- **Foreign Key:** `user_id` references `User(id)`
- **Relationships:**
  - Many-to-one with `User`

## 5. Topic
- **Primary Key:** `id`
- **Relationships:**
  - Many-to-many with `Message` (via `MessageTopic`)

## 6. MessageTopic (Join Table)
- **Foreign Keys:**
  - `message_id` references `Message(id)`
  - `topic_id` references `Topic(id)`
- **Composite Primary Key:** (`message_id`, `topic_id`)
- **Relationships:**
  - Many-to-one with `Message`
  - Many-to-one with `Topic`

---

## Indexes & Constraints
- **Foreign key constraints** on all relationships for referential integrity.
- **Indexes** on foreign keys (`user_id`, `conversation_id`, `topic_id`, etc.) for fast lookups.
- **Composite index** on `MessageTopic(message_id, topic_id)` for efficient many-to-many queries.
- **Timestamps** (e.g., `created_at`, `timestamp`) on key tables for sorting and querying by recency.

---

This document defines the relationships, foreign keys, and indexing strategy for the Freya backend database. It ensures data consistency and efficient querying as the project scales.
