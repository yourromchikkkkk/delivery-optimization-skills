---
name: code-review
description: >-
  Reviews code for quality, security, and maintainability using Splice standards (TypeScript, TypeScript: Next.js). Use when reviewing pull requests, diffs, or when the user asks for code review or feedback.
---

# Splice Code Review

Review changes against the standards below. Be specific: cite file/line, explain the rule, and suggest a fix.

## Context

- **Language**: TypeScript
- **Framework**: TypeScript: Next.js
- **Methodologies**: Clean Code, SOLID
- **Contact**: roman.korin@intellecteu.com
- **Standards dated**: 13.05.2026

## Style and naming

- **Indentation**: Spaces
- **Indent size (if spaces)**: 2 spaces
- **Quote style for strings**: Single quotes
- **Maximum line length**: 100
- **Trailing commas in multi-line collections**: Required
- **Type annotations / hints**: Required on all functions
- **File / module naming**: kebab-case
- **Class naming**: PascalCase
- **Function and variable naming**: camelCase
- **Constants**: UPPER_SNAKE_CASE
- **Test files**: <module>.test
- **Boolean variables prefix**: isX/hasX/shouldX

## Required patterns (must have)

- Typed schemas / DTOs for API request and response models
- Dependency injection via constructors (no global singletons)
- Typed HTTP clients (no raw requests / fetch in business code)
- Errors propagate via exceptions (no returning null on failure)
- App Router patterns: server components by default, 'use client' only when needed
- Server actions for mutations (no implicit API routes)
- next/image for images, next/font for fonts
- Single Responsibility — each module / class has one reason to change
- Open/Closed — open for extension, closed for modification
- Liskov Substitution — derived types must be substitutable for their base types
- Interface Segregation — many specific interfaces over one large interface
- Dependency Inversion — depend on abstractions, never on concretions

## Forbidden patterns (blockers)

- SQL string concatenation (only parameterized queries)
- eval / exec / pickle on untrusted input
- Bare except / catch-all without logging
- Hardcoded secrets / API keys / connection strings
- console.log / print left in committed code
- Wildcard imports
- Disabled lint or type-check rules without justification
- TODO / FIXME without a ticket reference
- any type used to bypass type-checking (use unknown + narrowing instead)
- @ts-ignore without an explanatory comment and ticket
- Non-null assertion (!) on values not provably non-null
- Client-side state in server components
- Direct DB access from client components
- Comments that describe *what* the code does (rewrite the code to be self-explanatory)
- Duplicated logic across files (DRY — extract a function or module)
- Dead / commented-out code blocks

## Warnings (non-blocking)

- Functions longer than 50 lines
- Cyclomatic complexity > 10
- More than 3 levels of nesting
- Magic numbers (constants without named meaning)
- Functions doing more than one thing (single-responsibility at function level)
- Functions with more than 3 arguments (use a parameter object)
- Boolean flag arguments (split into two named functions instead)
- Variable / parameter names of one or two letters (except loop counters)

## Testing

- **Test framework**: Vitest
- **Coverage minimum for new code**: 80%
- Critical user flows have end-to-end tests
- **HTTP mocking approach**: msw

## Security

- Input validation at all API boundaries
- Auth middleware on every endpoint by default (deny-by-default)
- Output escaping for user-rendered content
- Secrets only via secret manager (no .env files in repos)

## Tooling (CI enforces these)

- **Formatter**: Prettier
- **Linter**: ESLint
- **Type checker**: tsc strict

## Do not flag in review (already automated or out of scope)

- Formatting (handled by formatter)
- Import order
- Trailing whitespace / line endings
- Anything covered by an existing CI lint job
- Docstring wording / grammar

## Review workflow

1. Understand the change goal and affected areas.
2. Check **forbidden** and **security** items first — these are merge blockers.
3. Verify **required patterns** and **testing** expectations.
4. Note **warnings** and style/naming issues as non-blocking suggestions.
5. Skip anything listed under **Do not flag**.

## Feedback format

Group findings by severity:

- **Critical** — forbidden pattern, security issue, or missing required pattern; must fix before merge.
- **Suggestion** — warning thresholds, style, or maintainability; should fix or justify.
- **Nice to have** — optional polish.

For each finding: location → rule violated → recommended fix.
