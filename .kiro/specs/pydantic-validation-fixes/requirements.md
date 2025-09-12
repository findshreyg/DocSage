# Requirements Document

## Introduction

The DocSage microservices architecture is experiencing startup failures due to Pydantic validation errors across multiple services. The issues stem from using deprecated Pydantic v1 syntax in a Pydantic v2 environment, including deprecated `validator` decorators and malformed regex patterns in Field definitions. This feature will systematically update all schema files to use modern Pydantic v2 syntax and fix validation errors.

## Requirements

### Requirement 1

**User Story:** As a developer, I want all microservices to start successfully without Pydantic validation errors, so that the DocSage application can run properly.

#### Acceptance Criteria

1. WHEN any microservice starts THEN the system SHALL NOT throw Pydantic validation errors related to deprecated syntax
2. WHEN schema validation occurs THEN the system SHALL use Pydantic v2 compatible field validators
3. WHEN regex patterns are defined in Field constraints THEN the system SHALL use properly escaped regex syntax

### Requirement 2

**User Story:** As a developer, I want consistent validation patterns across all services, so that the codebase is maintainable and follows modern Pydantic best practices.

#### Acceptance Criteria

1. WHEN field validation is required THEN the system SHALL use `field_validator` decorator instead of deprecated `validator`
2. WHEN regex patterns are used in Field definitions THEN the system SHALL use the `pattern` parameter with properly formatted regex strings
3. WHEN validation methods are defined THEN the system SHALL follow Pydantic v2 syntax conventions

### Requirement 3

**User Story:** As a developer, I want all existing validation logic to be preserved during the migration, so that business rules and data integrity are maintained.

#### Acceptance Criteria

1. WHEN validation rules are updated THEN the system SHALL maintain the same validation behavior as before
2. WHEN password complexity validation occurs THEN the system SHALL enforce the same security requirements
3. WHEN file hash validation occurs THEN the system SHALL maintain the same format requirements
4. WHEN field constraints are applied THEN the system SHALL preserve existing length and format restrictions

### Requirement 4

**User Story:** As a developer, I want comprehensive validation across all schema files, so that no service has validation inconsistencies.

#### Acceptance Criteria

1. WHEN auth service schemas are processed THEN the system SHALL fix regex pattern syntax errors
2. WHEN conversation service schemas are processed THEN the system SHALL update validator decorators to field_validator
3. WHEN file service schemas are processed THEN the system SHALL update validator decorators to field_validator  
4. WHEN LLM service schemas are processed THEN the system SHALL update validator decorators to field_validator
5. WHEN all services are updated THEN the system SHALL have consistent Pydantic v2 syntax across all schema files