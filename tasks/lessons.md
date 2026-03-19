# Lessons Learned

## 2026-03-19: Dashboard Table Virtualization Performance Fix

### Problem
The dashboard was rendering all 261 company rows in the DOM simultaneously, causing:
- Layout thrashing with complex per-row elements (dropdowns, inputs, badges)
- All rows in DOM without virtualization
- Inline functions recreated on every render
- All rows re-rendering on any state change

### Solution Implemented
1. **VirtualTable component** - Only renders visible rows + 5-row buffer above/below
   - Uses `ResizeObserver` to track container height
   - Calculates visible row range based on scroll position
   - Uses CSS `translateY` for positioning rows within fixed-height container

2. **MemoizedCompanyRow** - `React.memo()` wrapped row component
   - Custom comparison function checking `id`, `status`, `owner`, `contact_email`, `isSelected`, `index`
   - Prevents re-renders when unrelated state changes

3. **Debounced search** - 300ms debounce via `useDebounce` hook
   - Reduces API calls during typing

4. **useCallback for handlers** - `updateCompanyField` and `toggleSelect` wrapped in `useCallback`
   - Prevents recreation on every render

### Key Takeaways
- For large tables (200+ rows), virtualization is essential for smooth scrolling
- `React.memo()` with custom comparison is powerful for complex row components
- Stable callback references (useCallback) are crucial for memoization to work
- Debouncing search input prevents unnecessary API calls and re-renders
