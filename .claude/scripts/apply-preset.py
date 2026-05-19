#!/usr/bin/env python3
"""
Interactive preset picker: choose language, framework, and methodologies at the
terminal, then write setup + form answers to code-standards.json from the preset
data defined in this file.

Usage:
    python .claude/scripts/apply-preset.py
    python .claude/scripts/apply-preset.py --from-config   # use setup already in JSON
    python .claude/scripts/apply-preset.py --fill-empty-only
"""
import argparse
import sys
from pathlib import Path

from standards_store import (
    DEFAULT_STANDARDS_PATH,
    index_questions,
    is_empty_value,
    load,
    question_value,
    read_setup,
    save,
    write_setup,
)


# ============================================================
# PRESET DATA
# ============================================================
# Conventions:
#   Keys map to question IDs in the Form sheet.
#   Special key "_additions" maps target-IDs (text-type rows) -> list of bullet lines.
#   Special key "_other_text" maps form-id -> text written into column E (the "If Other" column).

LANGUAGE_PRESETS = {
    "Python": {
        "style.indent": "Spaces",
        "style.size":   "4 spaces",
        "style.quotes": "Double quotes",
        "style.linelen": "100",
        "style.trailing": "Required",
        "style.types":  "Required on public functions only",
        "name.file":    "snake_case",
        "name.class":   "PascalCase",
        "name.func":    "snake_case",
        "name.const":   "UPPER_SNAKE_CASE",
        "name.test":    "test_<module>",
        "name.bool":    "is_/has_/should_",
        "test.fw":      "pytest",
        "test.cov":     "80%",
        "test.mock":    "respx",
        "tool.fmt":     "Black",
        "tool.lint":    "Ruff",
        "tool.types":   "mypy",
        # Forbidden defaults common in Python
        "fb.sql": "Y", "fb.eval": "Y", "fb.bare": "Y", "fb.secrets": "Y",
        "fb.mut": "Y", "fb.dborm": "Y", "fb.print": "Y", "fb.wildcard": "Y",
        "fb.disabled": "Y", "fb.todo": "Y",
        # Required defaults
        "req.dto": "Y", "req.di": "Y", "req.http": "Y", "req.exc": "Y",
        # Skip defaults
        "skip.fmt": "Y", "skip.imp": "Y", "skip.ws": "Y", "skip.lint": "Y",
        # Security defaults
        "sec.input": "Y", "sec.auth": "Y", "sec.secrets": "Y", "sec.authlib": "Y", "sec.crypto": "Y",
    },

    "TypeScript": {
        "style.indent": "Spaces",
        "style.size":   "2 spaces",
        "style.quotes": "Single quotes",
        "style.linelen": "100",
        "style.trailing": "Required",
        "style.types":  "Required on all functions",
        "name.file":    "kebab-case",
        "name.class":   "PascalCase",
        "name.func":    "camelCase",
        "name.const":   "UPPER_SNAKE_CASE",
        "name.test":    "<module>.test",
        "name.bool":    "isX/hasX/shouldX",
        "test.fw":      "Vitest",
        "test.cov":     "80%",
        "test.mock":    "msw",
        "tool.fmt":     "Prettier",
        "tool.lint":    "ESLint",
        "tool.types":   "tsc strict",
        "fb.sql": "Y", "fb.eval": "Y", "fb.secrets": "Y", "fb.print": "Y",
        "fb.wildcard": "Y", "fb.disabled": "Y", "fb.todo": "Y", "fb.bare": "Y",
        "req.dto": "Y", "req.di": "Y", "req.http": "Y", "req.exc": "Y",
        "skip.fmt": "Y", "skip.imp": "Y", "skip.ws": "Y", "skip.lint": "Y",
        "sec.input": "Y", "sec.auth": "Y", "sec.secrets": "Y", "sec.escape": "Y",
        "_additions": {
            "fb.other": [
                "any type used to bypass type-checking (use unknown + narrowing instead)",
                "@ts-ignore without an explanatory comment and ticket",
                "Non-null assertion (!) on values not provably non-null",
            ],
        },
    },

    "JavaScript": {
        "style.indent": "Spaces",
        "style.size":   "2 spaces",
        "style.quotes": "Single quotes",
        "style.linelen": "100",
        "style.trailing": "Required",
        "style.types":  "Not used",
        "name.file":    "kebab-case",
        "name.class":   "PascalCase",
        "name.func":    "camelCase",
        "name.const":   "UPPER_SNAKE_CASE",
        "name.test":    "<module>.test",
        "name.bool":    "isX/hasX/shouldX",
        "test.fw":      "Jest",
        "test.cov":     "80%",
        "test.mock":    "msw",
        "tool.fmt":     "Prettier",
        "tool.lint":    "ESLint",
        "tool.types":   "Not applicable",
        "fb.sql": "Y", "fb.eval": "Y", "fb.secrets": "Y", "fb.print": "Y",
        "fb.wildcard": "Y", "fb.disabled": "Y", "fb.todo": "Y",
        "req.dto": "N", "req.di": "Y", "req.http": "Y", "req.exc": "Y",
        "skip.fmt": "Y", "skip.imp": "Y", "skip.ws": "Y", "skip.lint": "Y",
        "sec.input": "Y", "sec.auth": "Y", "sec.secrets": "Y", "sec.escape": "Y",
        "_additions": {
            "fb.other": [
                "var keyword (use let / const)",
                "== / != (use === / !==)",
                "Unhandled promise rejections",
            ],
        },
    },

    "Go": {
        "style.indent": "Tabs",
        "style.linelen": "No hard limit",
        "style.quotes": "Double quotes",
        "style.types":  "Required on all functions",
        "name.file":    "snake_case",
        "name.class":   "PascalCase",
        "name.func":    "PascalCase",   # exported; unexported camelCase
        "name.const":   "PascalCase",
        "name.test":    "<module>_test",
        "name.bool":    "isX/hasX/shouldX",
        "test.fw":      "Go testing + testify",
        "test.cov":     "80%",
        "test.mock":    "In-house mock client",
        "tool.fmt":     "gofmt",
        "tool.lint":    "golangci-lint",
        "tool.types":   "Not applicable",
        "fb.sql": "Y", "fb.secrets": "Y", "fb.todo": "Y", "fb.disabled": "Y",
        "fb.print": "Y",
        "req.di": "Y", "req.http": "Y", "req.exc": "N",
        "skip.fmt": "Y", "skip.imp": "Y", "skip.ws": "Y", "skip.lint": "Y",
        "sec.input": "Y", "sec.auth": "Y", "sec.secrets": "Y",
        "_additions": {
            "fb.other": [
                "Ignored errors (assigning to _ without justification)",
                "Goroutine leaks (no context cancellation path)",
                "init() functions for side effects",
                "panic in library code (return error instead)",
            ],
            "req.other": [
                "Errors wrapped with fmt.Errorf(\"...: %w\", err) for context",
                "context.Context as the first parameter for any I/O function",
            ],
        },
    },

    "Java": {
        "style.indent": "Spaces",
        "style.size":   "4 spaces",
        "style.quotes": "Double quotes",
        "style.linelen": "120",
        "style.types":  "Required on all functions",
        "name.file":    "PascalCase",
        "name.class":   "PascalCase",
        "name.func":    "camelCase",
        "name.const":   "UPPER_SNAKE_CASE",
        "name.test":    "<module>_test",
        "name.bool":    "isX/hasX/shouldX",
        "test.fw":      "JUnit",
        "test.cov":     "80%",
        "tool.fmt":     "google-java-format",
        "tool.lint":    "checkstyle",
        "tool.types":   "javac",
        "fb.sql": "Y", "fb.secrets": "Y", "fb.todo": "Y", "fb.disabled": "Y",
        "fb.bare": "Y",
        "req.dto": "Y", "req.di": "Y", "req.http": "Y", "req.exc": "Y",
        "skip.fmt": "Y", "skip.imp": "Y", "skip.ws": "Y", "skip.lint": "Y",
        "sec.input": "Y", "sec.auth": "Y", "sec.secrets": "Y", "sec.escape": "Y",
        "_additions": {
            "fb.other": [
                "Raw types in generics (e.g. List instead of List<String>)",
                "Catching Exception or Throwable in business code",
                "Using @SuppressWarnings without justification",
            ],
        },
    },

    "Kotlin": {
        "style.indent": "Spaces",
        "style.size":   "4 spaces",
        "style.quotes": "Double quotes",
        "style.linelen": "120",
        "style.types":  "Required on public functions only",
        "name.file":    "PascalCase",
        "name.class":   "PascalCase",
        "name.func":    "camelCase",
        "name.const":   "UPPER_SNAKE_CASE",
        "name.test":    "<module>_test",
        "name.bool":    "isX/hasX/shouldX",
        "test.fw":      "JUnit",
        "test.cov":     "80%",
        "tool.fmt":     "ktlint",
        "tool.lint":    "ktlint",
        "tool.types":   "Not applicable",
        "fb.sql": "Y", "fb.secrets": "Y", "fb.todo": "Y", "fb.bare": "Y",
        "req.di": "Y", "req.http": "Y", "req.immutable": "Y",
        "skip.fmt": "Y", "skip.imp": "Y", "skip.ws": "Y", "skip.lint": "Y",
        "sec.input": "Y", "sec.auth": "Y", "sec.secrets": "Y",
        "_additions": {
            "fb.other": [
                "!! (non-null assertion) without proven non-null source",
                "lateinit on values that could be properly initialized in constructor",
            ],
        },
    },

    "C#": {
        "style.indent": "Spaces",
        "style.size":   "4 spaces",
        "style.quotes": "Double quotes",
        "style.linelen": "120",
        "style.types":  "Required on all functions",
        "name.file":    "PascalCase",
        "name.class":   "PascalCase",
        "name.func":    "PascalCase",
        "name.const":   "PascalCase",
        "name.test":    "<module>_test",
        "name.bool":    "isX/hasX/shouldX",
        "test.fw":      "NUnit / xUnit",
        "test.cov":     "80%",
        "tool.fmt":     "dotnet format",
        "tool.lint":    "None enforced",
        "tool.types":   "Not applicable",
        "fb.sql": "Y", "fb.secrets": "Y", "fb.todo": "Y", "fb.bare": "Y", "fb.disabled": "Y",
        "req.dto": "Y", "req.di": "Y", "req.http": "Y", "req.exc": "Y",
        "skip.fmt": "Y", "skip.imp": "Y", "skip.ws": "Y", "skip.lint": "Y",
        "sec.input": "Y", "sec.auth": "Y", "sec.secrets": "Y", "sec.escape": "Y",
        "_additions": {
            "fb.other": [
                "Async void methods (except for event handlers)",
                "Catching System.Exception in business code",
                "Synchronous calls (.Result / .Wait()) on async APIs",
            ],
        },
    },

    "Rust": {
        "style.indent": "Spaces",
        "style.size":   "4 spaces",
        "style.linelen": "100",
        "style.types":  "Required on all functions",
        "name.file":    "snake_case",
        "name.class":   "PascalCase",
        "name.func":    "snake_case",
        "name.const":   "UPPER_SNAKE_CASE",
        "name.test":    "test_<module>",
        "name.bool":    "is_/has_/should_",
        "test.fw":      "Other",
        "_other_text":  {"test.fw": "Cargo + built-in test framework"},
        "tool.fmt":     "rustfmt",
        "tool.lint":    "Clippy",
        "tool.types":   "Not applicable",
        "fb.sql": "Y", "fb.secrets": "Y", "fb.todo": "Y", "fb.disabled": "Y",
        "req.di": "N", "req.immutable": "Y", "req.exc": "N",
        "skip.fmt": "Y", "skip.imp": "Y", "skip.ws": "Y", "skip.lint": "Y",
        "sec.input": "Y", "sec.auth": "Y", "sec.secrets": "Y",
        "_additions": {
            "fb.other": [
                "unwrap() / expect() in production paths (use ? or proper error handling)",
                "unsafe blocks without a comment explaining the invariant",
                ".clone() to silence borrow-checker errors instead of fixing the design",
            ],
            "req.other": [
                "Errors via Result<T, E> with a domain-specific error type (use thiserror)",
                "Avoid panics in library code",
            ],
        },
    },

    "Ruby": {
        "style.indent": "Spaces",
        "style.size":   "2 spaces",
        "style.quotes": "Single quotes",
        "style.linelen": "120",
        "style.types":  "Optional / encouraged",
        "name.file":    "snake_case",
        "name.class":   "PascalCase",
        "name.func":    "snake_case",
        "name.const":   "UPPER_SNAKE_CASE",
        "name.test":    "<module>_test",
        "name.bool":    "is_/has_/should_",
        "test.fw":      "RSpec",
        "test.cov":     "80%",
        "tool.fmt":     "rubocop --fix",
        "tool.lint":    "rubocop",
        "tool.types":   "Sorbet",
        "fb.sql": "Y", "fb.eval": "Y", "fb.secrets": "Y", "fb.print": "Y", "fb.todo": "Y",
        "req.di": "Y", "req.http": "Y", "req.exc": "Y",
        "skip.fmt": "Y", "skip.imp": "Y", "skip.ws": "Y", "skip.lint": "Y",
        "sec.input": "Y", "sec.auth": "Y", "sec.secrets": "Y", "sec.escape": "Y",
    },

    "DAML": {
        "style.indent": "Spaces",
        "style.size":   "2 spaces",
        "style.linelen": "100",
        "style.types":  "Required on all functions",
        "name.file":    "PascalCase",
        "name.class":   "PascalCase",  # templates
        "name.func":    "camelCase",
        "name.const":   "UPPER_SNAKE_CASE",
        "name.test":    "Other",
        "_other_text":  {"name.test": "Test.<Module> with scenario-style tests"},
        "name.bool":    "is_/has_/should_",
        "test.fw":      "DAML scenarios",
        "test.cov":     "Other",
        "tool.fmt":     "damlc fmt",
        "tool.lint":    "daml lint",
        "tool.types":   "Not applicable",
        "fb.todo": "Y", "fb.secrets": "Y",
        "req.exc": "N", "req.immutable": "Y", "req.pure": "Y",
        "skip.fmt": "Y", "skip.ws": "Y",
        "sec.input": "Y",
        "_additions": {
            "fb.other": [
                "Choices that mutate state without explicit signatory authorization",
                "Templates without explicit ensure clauses for invariants",
                "Templates without explicit observer fields",
                "Use of partial functions (head, fromSome) — match exhaustively instead",
                "Hardcoded party identifiers in code (use Parties module / config)",
            ],
            "req.other": [
                "Every template declares signatory and observer fields explicitly",
                "Every template has an ensure clause documenting invariants",
                "Use ContractId<T> instead of arbitrary identifiers",
                "Use scenarios in Test.* modules to verify happy and unhappy paths",
                "Use the Daml-Trigger / Daml-Script SDKs for off-ledger workflows",
            ],
            "warn.other": [
                "Choices longer than 20 lines — split into helper functions",
                "Templates with more than 8 fields — consider splitting",
            ],
        },
    },
}


FRAMEWORK_PRESETS = {
    "Python: Django": {
        "test.fw": "pytest",
        "_additions": {
            "req.other": [
                "Use Django REST Framework serializers for API request/response",
                "Use class-based views; avoid function-based views in new code",
                "Database queries via repository / service layer, not from views",
            ],
            "fb.other": [
                "raw() ORM calls without parameterization",
                "Logic in Django templates beyond simple presentation",
                "Direct ORM access from views (must go through services / repositories)",
                "select_related / prefetch_related missing on related-field access",
            ],
        },
    },

    "Python: FastAPI": {
        "_additions": {
            "req.other": [
                "Pydantic v2 models for every request and response schema",
                "Depends() for dependency injection (auth, DB session, services)",
                "BackgroundTasks or a proper queue (Celery / Arq) for async work",
                "Async route handlers — never perform blocking I/O inside them",
            ],
            "fb.other": [
                "Returning ORM objects directly from endpoints (use response_model)",
                "Globals / module-level state for request-scoped values",
            ],
        },
    },

    "Python: Flask": {
        "_additions": {
            "req.other": [
                "Use Blueprints to organize routes; one blueprint per feature",
                "Validate request payloads with marshmallow or pydantic",
                "Use Flask-Login or a centralized auth decorator on every endpoint",
            ],
            "fb.other": [
                "Logic inside route functions (move to a service layer)",
            ],
        },
    },

    "Python: Pyramid": {
        "_additions": {
            "req.other": [
                "Configure routes via cornice or pyramid.config — never via decorators alone",
            ],
        },
    },

    "Python: Data / ML (pandas, numpy, sklearn)": {
        "name.file": "snake_case",
        "test.cov": "70%",
        "_additions": {
            "req.other": [
                "Notebooks live in notebooks/ and are version-controlled with cleared outputs (nbstripout)",
                "Reusable code goes into installable modules, not notebooks",
                "Random seeds are explicit and configurable",
                "Dataset loading is wrapped in a function with a docstring describing the source",
            ],
            "fb.other": [
                "Inplace mutation in pandas (df.fillna(..., inplace=True)) — return new frames",
                "Chained indexing (df[a][b]) — use .loc[a, b]",
                "Hardcoded file paths in code (use a config module / argparse)",
            ],
        },
    },

    "JavaScript: React": {"_includes": ["__React"]},
    "TypeScript: React": {"_includes": ["__React"]},
    "JavaScript: Vue":   {"_includes": ["__Vue"]},
    "TypeScript: Vue":   {"_includes": ["__Vue"]},
    "JavaScript: Angular": {"_includes": ["__Angular"]},
    "TypeScript: Angular": {"_includes": ["__Angular"]},
    "JavaScript: Node.js (Express)": {"_includes": ["__Node"]},
    "TypeScript: Node.js (Express)": {"_includes": ["__Node"]},
    "JavaScript: Next.js": {"_includes": ["__Next"]},
    "TypeScript: Next.js": {"_includes": ["__Next"]},
    "TypeScript: NestJS": {
        "_additions": {
            "req.other": [
                "Modules organized by feature; each module exports its own controller, service, repository",
                "Dependency injection via NestJS providers — never instantiate services manually",
                "Validation via class-validator and class-transformer on every DTO",
                "Use Guards for authorization on every controller",
            ],
            "fb.other": [
                "Business logic inside controllers (must live in services)",
                "Direct repository access from controllers",
            ],
        },
    },

    "Go: standard library / net/http": {"_includes": ["__Go_HTTP"]},
    "Go: gin":  {"_includes": ["__Go_HTTP"]},
    "Go: echo": {"_includes": ["__Go_HTTP"]},
    "Go: chi":  {"_includes": ["__Go_HTTP"]},

    "Java: Spring Boot": {"_includes": ["__Spring"]},
    "Kotlin: Spring Boot": {"_includes": ["__Spring"]},
    "Java: Quarkus":   {"_includes": ["__Spring"]},
    "Kotlin: Ktor":    {
        "_additions": {
            "req.other": [
                "Routes organized in Routing { } with nested route() calls per feature",
                "Use call.receive<DTO>() with kotlinx.serialization for input validation",
            ],
        },
    },

    "C#: ASP.NET Core": {
        "_additions": {
            "req.other": [
                "Controllers use [ApiController] attribute and inherit from ControllerBase",
                "Validation via FluentValidation or DataAnnotations on every DTO",
                "Dependency injection via the built-in container; register in Program.cs",
                "Services use async/await end-to-end",
            ],
            "fb.other": [
                "Static service locators (depend on DI instead)",
                ".Result / .Wait() on async calls",
            ],
        },
    },

    "C#: .NET (general)": {
        "_additions": {
            "req.other": [
                "Use IDisposable / using for any resource that owns native or unmanaged state",
            ],
        },
    },

    "Rust: Axum / Actix": {
        "_additions": {
            "req.other": [
                "Errors implement IntoResponse / ResponseError to surface as HTTP responses",
                "Extractors used for request parsing — no manual parsing of bodies",
                "tower / actix middleware for auth and logging",
            ],
        },
    },

    "Ruby: Rails": {
        "_additions": {
            "req.other": [
                "Service objects in app/services/ for any logic beyond a few lines",
                "Strong Parameters on every controller action",
                "Active Record callbacks limited to data integrity (no business logic)",
            ],
            "fb.other": [
                "Logic in Rails views (use partials / view objects)",
                "Direct SQL via find_by_sql / connection.execute without parameterization",
            ],
        },
    },

    "DAML: smart contracts": {
        "_additions": {
            "req.other": [
                "Each template declares signatories, observers, and key fields explicitly",
                "Choices use exercise-only patterns — never modify template state outside choices",
                "Use ContractId<T> as the type for cross-template references",
            ],
            "fb.other": [
                "Templates without ensure clauses for non-trivial invariants",
                "Off-ledger logic in templates (move to Daml-Script / Daml-Trigger)",
            ],
        },
    },
}

# Internal includes (referenced via "_includes")
_INCLUDES = {
    "__React": {
        "name.file": "PascalCase",  # for components — leaves this open
        "_additions": {
            "req.other": [
                "Functional components with hooks (no class components)",
                "Props typed via interface or type alias for every component",
                "useEffect dependencies are exhaustive (eslint-plugin-react-hooks)",
                "Component files: one default export per file",
            ],
            "fb.other": [
                "Components longer than 200 lines (split into smaller components)",
                "Inline styles (use CSS modules, Tailwind, or styled-components)",
                "Direct DOM manipulation (use refs only when there is no alternative)",
                "Stateful logic outside of components (use custom hooks instead)",
            ],
        },
    },
    "__Vue": {
        "_additions": {
            "req.other": [
                "Use the Composition API for new components",
                "Single-file components (.vue) — script + template + style co-located",
                "Props validated with the type / required / default syntax",
            ],
            "fb.other": [
                "Mixins (use composables instead)",
                "Direct DOM manipulation outside of refs",
            ],
        },
    },
    "__Angular": {
        "_additions": {
            "req.other": [
                "Standalone components for new code (no NgModules unless required by a library)",
                "OnPush change detection by default",
                "Reactive forms for any form with more than 2 fields",
                "Services provided in root unless they have explicit per-feature scope",
            ],
            "fb.other": [
                "any in component / service signatures",
                "Subscriptions without takeUntilDestroyed / async pipe (memory leaks)",
            ],
        },
    },
    "__Node": {
        "_additions": {
            "req.other": [
                "Routes organized by feature (one router file per resource)",
                "Validation via zod / yup / joi on every endpoint",
                "Centralized error-handling middleware",
                "Async handlers wrapped to forward errors to the error middleware",
            ],
            "fb.other": [
                "Synchronous fs.* APIs in request handlers",
                "Hardcoded ports / hosts (use env config)",
            ],
        },
    },
    "__Next": {
        "_additions": {
            "req.other": [
                "App Router patterns: server components by default, 'use client' only when needed",
                "Server actions for mutations (no implicit API routes)",
                "next/image for images, next/font for fonts",
            ],
            "fb.other": [
                "Client-side state in server components",
                "Direct DB access from client components",
            ],
        },
    },
    "__Go_HTTP": {
        "_additions": {
            "req.other": [
                "Handlers thin: parse → call service → encode response",
                "context.Context propagated through every layer",
                "Errors mapped to status codes via a single error mapper",
            ],
            "fb.other": [
                "Logic in handlers (move to services)",
                "Goroutines spawned per request without context cancellation",
            ],
        },
    },
    "__Spring": {
        "_additions": {
            "req.other": [
                "Layered: @RestController → @Service → @Repository — never skip layers",
                "Constructor injection (no field injection / @Autowired on fields)",
                "Validation via @Valid on controller params and @NotNull / @Size on DTO fields",
                "Use Spring Profiles for environment-specific config",
            ],
            "fb.other": [
                "Field injection via @Autowired",
                "Business logic in @Repository methods",
                "@Transactional on @Repository methods (belongs on @Service)",
            ],
        },
    },
}


METHODOLOGY_PRESETS = {
    "method.clean_code": {
        "warn.fnlen": "Y", "warn.cmplx": "Y", "warn.nest": "Y", "warn.magic": "Y",
        "_additions": {
            "warn.other": [
                "Functions doing more than one thing (single-responsibility at function level)",
                "Functions with more than 3 arguments (use a parameter object)",
                "Boolean flag arguments (split into two named functions instead)",
                "Variable / parameter names of one or two letters (except loop counters)",
            ],
            "fb.other": [
                "Comments that describe *what* the code does (rewrite the code to be self-explanatory)",
                "Duplicated logic across files (DRY — extract a function or module)",
                "Dead / commented-out code blocks",
            ],
        },
    },

    "method.solid": {
        "_additions": {
            "req.other": [
                "Single Responsibility — each module / class has one reason to change",
                "Open/Closed — open for extension, closed for modification",
                "Liskov Substitution — derived types must be substitutable for their base types",
                "Interface Segregation — many specific interfaces over one large interface",
                "Dependency Inversion — depend on abstractions, never on concretions",
            ],
        },
    },

    "method.ddd": {
        "_additions": {
            "req.other": [
                "Domain logic isolated from infrastructure (no DB / HTTP imports in domain)",
                "Entities have identity; value objects are immutable and equality-by-value",
                "Aggregates have a single root; modify aggregate state only via the root",
                "Repositories return aggregate roots, not arbitrary entities",
                "Ubiquitous language consistent with domain experts (no Manager / Helper / Util in domain)",
            ],
            "fb.other": [
                "Bypassing the aggregate root to mutate inner entities directly",
                "Domain types depending on framework / DB types",
            ],
        },
    },

    "method.hex": {
        "_additions": {
            "req.other": [
                "Domain core has zero dependencies on frameworks, DB, or HTTP",
                "External services accessed via ports (interfaces) defined in the domain",
                "Adapters (HTTP, DB, message queue) implement the ports",
                "Tests can run against the domain core without any infrastructure",
            ],
        },
    },

    "method.twelve": {
        "_additions": {
            "req.other": [
                "Config strictly via environment variables (no checked-in env files except samples)",
                "Treat backing services (DB, cache, queue) as attached resources via URI config",
                "Build / release / run are strictly separated stages",
                "Stateless processes; share-nothing architecture",
                "Logs as event streams to stdout/stderr — no log files written by the app",
                "Disposable processes — graceful shutdown on SIGTERM",
            ],
        },
    },

    "method.tdd": {
        "_additions": {
            "req.other": [
                "Write a failing test before writing production code (red → green → refactor)",
                "Each commit keeps the suite green; no broken tests left for later",
                "Tests describe behavior, not implementation",
            ],
        },
    },

    "method.functional": {
        "req.pure": "Y",
        "req.immutable": "Y",
        "_additions": {
            "req.other": [
                "Prefer pure functions in the core; isolate side effects at the edges",
                "Prefer immutable data structures and persistent collections",
                "Map / filter / reduce over hand-rolled loops where they read more clearly",
                "Avoid shared mutable state; pass data explicitly",
            ],
            "fb.other": [
                "Mutating function arguments",
                "Hidden global state",
            ],
        },
    },
}

NONE_FRAMEWORK = "None / not applicable"

METHODOLOGY_CHOICES = [
    ("method.clean_code", "Clean Code (Robert C. Martin)"),
    ("method.solid", "SOLID principles"),
    ("method.ddd", "Domain-Driven Design (DDD)"),
    ("method.hex", "Hexagonal / Ports & Adapters / Clean Architecture"),
    ("method.twelve", "12-Factor App"),
    ("method.tdd", "Test-Driven Development (TDD)"),
    ("method.functional", "Functional core / immutable data"),
]


# ============================================================
# Engine
# ============================================================
def is_yes(value) -> bool:
    if value is None:
        return False
    return str(value).strip().upper() in ("Y", "YES", "TRUE", "X", "1")


def frameworks_for_language(lang: str) -> list[str]:
    prefix = f"{lang}: "
    return sorted(k for k in FRAMEWORK_PRESETS if k.startswith(prefix))


def _default_index(options: list[str], current: str | None) -> int | None:
    if not current:
        return None
    cur = str(current).strip()
    if cur in options:
        return options.index(cur)
    return None


def _read_line(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise SystemExit(130) from None


def choose_one(title: str, options: list[str], *, current: str | None = None) -> str:
    """Numbered menu; returns the selected option string."""
    if not options:
        raise ValueError("choose_one requires at least one option")

    print(f"\n{title}")
    default_idx = _default_index(options, current)
    for i, label in enumerate(options, start=1):
        mark = " (current)" if default_idx == i - 1 else ""
        print(f"  {i}. {label}{mark}")

    hint = f"[1-{len(options)}]"
    if default_idx is not None:
        hint += f", Enter={default_idx + 1}"

    while True:
        raw = _read_line(f"Choose {hint}: ")
        if raw == "" and default_idx is not None:
            return options[default_idx]
        if raw.isdigit():
            n = int(raw)
            if 1 <= n <= len(options):
                return options[n - 1]
        print(f"  Enter a number from 1 to {len(options)}.")


def prompt_text(title: str, *, current: str | None = None, required: bool = False) -> str:
    """Ask for a single line of text."""
    print(f"\n{title}")
    if current:
        print(f"  (current: {current})")

    while True:
        hint = "Enter value"
        if current:
            hint += ", or press Enter to keep current"
        raw = _read_line(f"{hint}: ")
        if raw == "" and current:
            return current
        if raw == "" and not required:
            return ""
        if raw:
            return raw
        if required:
            print("  This field is required.")
        else:
            return ""


def choose_many(title: str, choices: list[tuple[str, str]], *, current: dict[str, str] | None = None) -> list[str]:
    """Multi-select menu; returns list of selected setup IDs."""
    current = current or {}
    default_on = {cid for cid, _ in choices if is_yes(current.get(cid))}

    print(f"\n{title}")
    print("  Enter numbers separated by commas (e.g. 1,3), 'all', 'none', or press Enter to keep current.")
    for i, (cid, label) in enumerate(choices, start=1):
        on = "Y" if cid in default_on else "N"
        print(f"  {i}. [{on}] {label}")

    default_raw = ",".join(str(i) for i, (cid, _) in enumerate(choices, start=1) if cid in default_on)

    while True:
        raw = _read_line("Choose: ").strip().lower()
        if raw == "" and default_on:
            return sorted(default_on)
        if raw in ("none", "n", "0"):
            return []
        if raw == "all":
            return [cid for cid, _ in choices]
        if raw.replace(" ", "") == "":
            return []
        try:
            picked = {int(part) for part in raw.split(",") if part.strip()}
        except ValueError:
            print("  Invalid input. Use numbers, 'all', or 'none'.")
            continue
        if not picked or any(n < 1 or n > len(choices) for n in picked):
            print(f"  Each number must be between 1 and {len(choices)}.")
            continue
        return [choices[n - 1][0] for n in sorted(picked)]


def prompt_meta_fields(data: dict) -> None:
    """Ask for department and contact; write to meta.team / meta.contact questions."""
    form_idx = index_questions(data)
    team_q = form_idx.get("meta.team")
    contact_q = form_idx.get("meta.contact")

    current_team = question_value(team_q) if team_q else None
    current_contact = question_value(contact_q) if contact_q else None

    department = prompt_text(
        "Department / team name",
        current=current_team,
        required=True,
    )
    contact = prompt_text(
        "Contact (Slack channel or email)",
        current=current_contact,
        required=True,
    )

    if team_q:
        team_q["suggested"] = department
        print(f"  meta.team = {department}")
    if contact_q:
        contact_q["suggested"] = contact
        print(f"  meta.contact = {contact}")


def prompt_setup_interactive(existing: dict | None = None) -> dict:
    """Ask the user for language, framework, and methodologies."""
    existing = existing or {}

    languages = sorted(LANGUAGE_PRESETS.keys())
    lang = choose_one(
        "Primary language",
        languages,
        current=existing.get("setup.lang"),
    )

    fw_options = frameworks_for_language(lang)
    fw_options.append(NONE_FRAMEWORK)
    framework = choose_one(
        "Framework / runtime",
        fw_options,
        current=existing.get("setup.framework"),
    )

    selected_methods = choose_many(
        "Methodologies (multi-select)",
        METHODOLOGY_CHOICES,
        current=existing,
    )

    setup = {
        "setup.lang": lang,
        "setup.framework": framework,
    }
    for method_id in METHODOLOGY_PRESETS:
        setup[method_id] = "Y" if method_id in selected_methods else "N"

    return setup


def collect_presets(setup: dict):
    """Return list of preset dicts (in order: language, framework, methodologies)."""
    presets = []
    lang = (setup.get("setup.lang") or "").strip()
    if lang and lang in LANGUAGE_PRESETS:
        presets.append((f"Language: {lang}", LANGUAGE_PRESETS[lang]))
    elif lang:
        print(f"  (no language preset for '{lang}' — skipping)")

    fw = (setup.get("setup.framework") or "").strip()
    if fw and fw in FRAMEWORK_PRESETS:
        # Resolve _includes
        fw_preset = dict(FRAMEWORK_PRESETS[fw])  # copy
        includes = fw_preset.pop("_includes", [])
        for inc in includes:
            if inc in _INCLUDES:
                merged_additions = dict(fw_preset.get("_additions", {}))
                inc_data = _INCLUDES[inc]
                for k, v in inc_data.items():
                    if k == "_additions":
                        for tgt, lines in v.items():
                            merged_additions.setdefault(tgt, []).extend(lines)
                    else:
                        fw_preset.setdefault(k, v)
                if merged_additions:
                    fw_preset["_additions"] = merged_additions
        presets.append((f"Framework: {fw}", fw_preset))
    elif fw and fw not in ("None / not applicable", ""):
        print(f"  (no framework preset for '{fw}' — skipping)")

    for m in METHODOLOGY_PRESETS:
        if is_yes(setup.get(m)):
            presets.append((f"Methodology: {m}", METHODOLOGY_PRESETS[m]))

    return presets


def apply(data: dict, presets, *, fill_empty_only: bool = False) -> None:
    """Apply preset values to form questions in JSON."""
    form_idx = index_questions(data)
    filled, additions, skipped = 0, 0, 0

    for source, preset in presets:
        print(f"\n• {source}")
        other_text = preset.get("_other_text", {})
        for qid, val in preset.items():
            if qid in ("_additions", "_includes", "_other_text"):
                continue
            if qid not in form_idx:
                skipped += 1
                continue
            q = form_idx[qid]
            if fill_empty_only and not is_empty_value(question_value(q)):
                continue
            q["suggested"] = val
            filled += 1
            if qid in other_text:
                q["other"] = other_text[qid]
            print(f"    set  {qid:18s} = {val}")

        for target, lines in preset.get("_additions", {}).items():
            if target not in form_idx:
                continue
            q = form_idx[target]
            if fill_empty_only:
                current = question_value(q) or ""
                current_lines = [ln for ln in str(current).splitlines() if ln.strip()]
                new_lines = [ln for ln in lines if ln not in current_lines]
                if not new_lines:
                    continue
                combined = "\n".join(current_lines + new_lines).strip()
                additions += len(new_lines)
                action_lines = new_lines
            else:
                combined = "\n".join(lines).strip()
                additions += len(lines)
                action_lines = lines
            q["suggested"] = combined
            for ln in action_lines:
                print(f"    add  {target:18s} + {ln}")

    mode = "empty fields only" if fill_empty_only else "all preset fields"
    print(
        f"\nSummary: updated {filled} fields, wrote {additions} rule lines ({mode}). "
        f"({skipped} preset keys skipped — no matching question)"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "config",
        nargs="?",
        default=str(DEFAULT_STANDARDS_PATH),
        help=f"Standards JSON path (default: {DEFAULT_STANDARDS_PATH})",
    )
    parser.add_argument(
        "--from-config",
        action="store_true",
        help="Use setup already saved in JSON (no prompts)",
    )
    parser.add_argument(
        "--fill-empty-only",
        action="store_true",
        help="Only write preset values into empty form fields (keep existing answers)",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    data = load(config_path)
    existing = read_setup(data)

    if args.from_config:
        setup = existing
        if not (setup.get("setup.lang") or "").strip():
            print(
                "No language in config. Run without --from-config to choose interactively.",
                file=sys.stderr,
            )
            sys.exit(1)
        print("Setup choices (from config):")
    else:
        print("Code standards preset picker")
        print("Preset data lives in apply-preset.py — choose your stack below.\n")
        setup = prompt_setup_interactive(existing)
        for method_id in METHODOLOGY_PRESETS:
            setup.setdefault(method_id, "N")
        write_setup(data, setup)
        print("\nYour choices:")
        for k, v in setup.items():
            if k.startswith("setup.") or is_yes(v):
                print(f"  {k} = {v}")

        prompt_meta_fields(data)

    presets = collect_presets(setup)
    if not presets:
        print("No presets matched. Check language / framework names.", file=sys.stderr)
        sys.exit(1)

    apply(data, presets, fill_empty_only=args.fill_empty_only)

    out = save(data, config_path)
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
