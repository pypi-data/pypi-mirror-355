**_This document will comprehensively outline a full integration test checklist. It may not be completely necessary to test all of these cases, depending on the scope of the changes. It's paramount to have thorough testing before going to production or even creating a staging build._**

_Ensure expected behavior is occurring for each of these._

##### General Edge Cases _\*\*important!_

-   [ ] Boot the plugin without POS open
-   [ ] Boot the plugin with POS open, and then close POS
-   [ ] Currently we do not have an easy way of clearing the persistent DB without PLUGIN_ID in index.ts... we should look into that as it's important for testing
-   [ ] "" Same for deleting the db file, also do the same for having an empty POS database.
-   [ ] Delete your last snippet, and also save the 'quicksave' snippet that should be offered to you
-   [ ] Would be good to double check the onboarding works

##### Feature Specific

**_Do for both the language view and sorted by recent.... if applicable_ \***For a more thorough test, also try out rapid firing on each of these.\*
_\*\*Edit_

-   [ ] Reclassify _(important for the language view)_
-   [ ] Edit description / title
        _\*\*Delete_
-   [ ] Delete snippet
        _\*\*Save_
-   [ ] Save from cell button
-   [ ] Save from right click menu
        _\*\*Share_
-   [ ] right click menu
-   [ ] pieces view (list of snippets)
        _\*\*Enrich_
-   [ ] Enrich from the context menu
        \*\*\*Expand
-   [ ] Expand a snippet
        \*\*\*Refresh
-   [ ] Refresh button
        _\*\*Search_
-   [ ] Search (both for long and short queries)
        _\*\*Discovery_
-   [ ] Run discovery on a notebook - [ ] make sure it passes - [ ] rapid fire as well
        _\*\*qGPT_
-   [ ] Send a normal query
-   [ ] try one of the hints
-   [ ] Rapid fire messages
-   [ ] open related file
-   [ ] code buttons (share, save, copy)
        _\*\*OCR Snippets_
-   [ ] OCR snippets behave differently in multiple cases so it's important to ensure the handling is proper here
-   [ ] reclassify
-   [ ] edit title
-   [ ] edit description

##### General UI

-   [ ] Ensure all language icons work
        obsidian://open?vault=Obsidian%20Vault&file=Obsidian%20Integration%20Testing

---
