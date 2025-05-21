# CLAUDE.md - Hydrophone Analyzer Development Strategy

This document outlines the development strategy for improving the Hydrophone Analyzer application. It serves as a living document to track tasks, decisions, and progress.

## Design Rules and Guidelines

### Core Development Principles

1. **Code Organization**
   - Edit existing modules rather than creating temporary/quick-fix modules
   - Only create new modules when required by architectural needs
   - Maintain clean directory structure by refactoring within existing files

2. **Incremental Development**
   - Make small, focused changes and test each change thoroughly
   - Avoid large-scale changes that could lead to untraceable issues
   - Document each change with its intended purpose and outcome

3. **Testing Methodology**
   - Develop test cases for each module to verify functionality
   - Implement automated tests where possible
   - Ensure each feature can be tested independently

4. **Logging and Verification**
   - Generate logs for all feature changes and tests
   - Verify feature operation through log analysis
   - Confirm functionality through user feedback

5. **Documentation**
   - Maintain DEVELOPMENT_LOG.md to track all testing and changes
   - Record when features were modified or tested
   - Create traceable history of development decisions

## Current Status Assessment

The Hydrophone Analyzer is currently a functional application with several technical challenges:

1. **UI Interaction Issues**:
   - Button handlers require special fixes via `direct_fix.py` and `state_buttons_fix.py`
   - Z-order problems with matplotlib components
   - Event handling reliability issues

2. **Navigation Instability**:
   - Time zoom functionality requiring special debug logging
   - Navigation controls needing additional fixes

3. **Error Management Challenges**:
   - Significant error logging infrastructure suggests recurring issues
   - Recovery mechanisms need enhancement

## Development Priority Areas

### 1. Stability Enhancements (Immediate Priority)

#### 1.1. Button Handler Consolidation
- [ ] Refactor button handling to use a consistent approach within existing modules
- [ ] Eliminate dependency on position-based button detection
- [ ] Implement more reliable event registration

#### 1.2. Navigation System Robustness
- [ ] Debug and fix the time zoom functionality
- [ ] Enhance spectrogram updating to prevent rendering issues
- [ ] Implement more granular debugging for navigation features

#### 1.3. Error Handling Improvement
- [ ] Create more robust recovery mechanisms for common errors
- [ ] Enhance error logging to provide actionable information
- [ ] Implement graceful degradation for non-critical failures

### 2. UI Architecture Modernization (Short-term)

#### 2.1. UI Framework Improvement
- [ ] Enhance the existing matplotlib approach with better practices
- [ ] Implement cleaner separation between UI elements and functionality
- [ ] Create more reliable event handling within the current framework

#### 2.2. Event System Overhaul
- [ ] Implement consistent event management pattern
- [ ] Improve event handling within existing modules
- [ ] Decouple event generation from handling

#### 2.3. UI Component Reorganization
- [ ] Consolidate UI creation functions within existing modules
- [ ] Create reusable UI patterns for consistency
- [ ] Implement consistent styling approach

### 3. Feature Enhancements (Medium-term)

#### 3.1. Visualization Improvements
- [ ] Add more visualization options (waterfall, contour, etc.)
- [ ] Implement customizable color schemes
- [ ] Add annotation capabilities for marking interesting features

#### 3.2. Analysis Tools
- [ ] Implement statistical analysis features for selected regions
- [ ] Add frequency band isolation capability
- [ ] Create comparison tools for different time segments

#### 3.3. Data Management
- [ ] Enhance file loading with progress indication
- [ ] Add support for more hydrophone data formats
- [x] Implement export functionality for processed data
- [x] Fix export format compatibility for re-import
- [x] Improve title display and button layout for better UI experience
- [x] Implement modal comment dialog for better user experience
- [x] Create dedicated comment list display for better comment organization
- [x] Fix comment system button text updates to reflect current operation
- [x] Implement comment selection display with enhanced formatting

## Testing Strategy

### Module Testing Approach

We will develop systematic testing for each module:

1. **UI Components Tests**
   - Verify button creation and event handling
   - Test UI element positioning and visibility
   - Validate user interaction workflows

2. **Navigation System Tests**
   - Test time zoom functionality with various data sizes
   - Verify navigation controls operate correctly
   - Ensure spectrogram updates appropriately with navigation changes

3. **Data Processing Tests**
   - Validate data loading from different file formats
   - Test data transformation and visualization pipelines
   - Verify correct handling of edge cases (empty files, malformed data)

4. **Visualization Tests**
   - Verify correct spectrogram rendering
   - Test FFT display functionality
   - Validate colormap and scaling functionality

### Test Documentation

All tests will be documented in DEVELOPMENT_LOG.md with:
- Date and time of testing
- Specific functionality tested
- Test inputs and expected outputs
- Actual results and observations
- Any issues discovered and their resolution

## Implementation Approach

### Phase 1: Stability Focus (Current)
Focus on addressing the most critical stability issues:
1. Improve button handling within existing modules
2. Fix navigation and zoom functionality
3. Enhance error recovery mechanisms

### Phase 2: Architecture Improvement
Once stability is achieved, focus on architectural improvements:
1. Refactor and consolidate UI creation functions
2. Implement a cleaner event handling system
3. Reorganize code for better maintainability

### Phase 3: Feature Enhancement
After architectural improvements, focus on new features:
1. Add new visualization capabilities
2. Implement additional analysis tools
3. Enhance data import/export functionality

## Decision Log

| Date       | Decision                                           | Rationale                                     |
|------------|----------------------------------------------------|--------------------------------------------|
| 2025-05-15 | Start tracking development strategy in CLAUDE.md   | Establish clear direction for improvement   |
| 2025-05-15 | Prioritize button handler refactoring              | Most immediate source of stability issues   |
| 2025-05-15 | Establish design rules for incremental development | Ensure code quality and maintainability    |
| 2025-05-15 | Create testing methodology with logging verification | Improve feature stability and tracking     |
| 2025-05-15 | Fix export file format to match original files     | Ensure compatibility for re-import functionality |
| 2025-05-15 | Adjust UI layout with smaller buttons and repositioned title | Prevent title-button overlap with long project names |
| 2025-05-19 | Implement textbox lag reduction strategies         | Improve comment input responsiveness       |
| 2025-05-21 | Switch to modal dialog for comment input           | Eliminate textbox lag and improve user experience |
| 2025-05-21 | Create dedicated comment list panel                | Better organize and manage multiple comments |
| 2025-05-21 | Use negative coordinate positioning for UI elements | Allow UI elements to extend beyond figure boundaries |

## Technical Debt Notes

- Button handling relies on axis position detection which is fragile
- Navigation system lacks proper error handling
- UI component creation is scattered across multiple functions
- Error logging is extensive but recovery mechanisms are limited
- State management is centralized but could benefit from better organization
- TextBox widgets experience lag due to matplotlib redrawing behavior

## Next Steps

1. Create DEVELOPMENT_LOG.md to track all testing and changes
2. Develop initial test cases for the button handling system
3. Begin incremental refactoring of the button handling approach within existing modules
4. Implement more comprehensive logging for the navigation system

---

This document will be updated regularly to reflect current development status, decisions, and priorities.