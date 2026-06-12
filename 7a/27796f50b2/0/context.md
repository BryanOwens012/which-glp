# Session Context

## User Prompts

### Prompt 1

Add to both the global and repo CLAUDE.md that we should be aggressively
  prefetching pages and queries. Basically, reword what I said:                        
                                                               
  Would it make sense that, to prefetch all                                
    pages and page tabs whenever the user lands on any of      
  them? Of course the prefetching would                        
    be done in the background and deferred/non-blocking        
       ...

### Prompt 2

Add to both the global and repo CLAUDE.md that, regardless of the size of the web app (such as the number of pages), we should be aggressively
  prefetching pages and queries:               
                                                               
prefetch all                                
    pages and page tabs whenever the user lands on any of      
  them. Of course the prefetching would                        
    be done in the background and deferred/non-blocking        
        ...

### Prompt 3

Add to both the global and repo CLAUDE.md:

  For all LLM calls, regardless of LLM provider, as long as prompt
  caching is available, we need to always be looking for 
  opportunities to implement aggressive prompt caching. Prompt
  caching dramatically cuts cost and increases speed. Search internet
  for more info on it that could inform best practices around prompt
  caching

 And also, add to both global and repo CLAUDE.md, as appropriate:     
  If we use Langfuse in the repo, then:        ...

### Prompt 4

and htne make any necessary code changes to comply with this repo CLAUDE.md

### Prompt 5

Now execute the following, in parallel if possible:

Go through all the changed files in this PR, one at a time, line by line, to confirm that you implemented it according to the spec and that it’s correct. Go through all the data paths, code/execution paths, and logical branching for all user journeys, including happy paths and sad paths.

Ensure that all UI/UX components are built correctly and to spec. It can help with intuition to decompose the components within the codebase, and decompose...

