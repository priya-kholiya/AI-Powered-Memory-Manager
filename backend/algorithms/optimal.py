
def optimal(process_id, memory_size, reference_string, frames):
    memory = [] 
    page_faults = 0
    steps = []

    n = len(reference_string)

    for i in range(n):
        page = reference_string[i]

        if page not in memory:
       
            if len(memory) < frames:
                memory.append(page)
            else:
                # Find the page that will not be used for the longest time
                farthest = -1
                replace_index = -1
                for j in range(len(memory)):
                    if memory[j] not in reference_string[i+1:]:
                        # This page is not used again → replace it
                        replace_index = j
                        break
                    else:
                        next_use = reference_string[i+1:].index(memory[j])
                        if next_use > farthest:
                            farthest = next_use
                            replace_index = j
                # Replace the chosen page
                memory[replace_index] = page

            page_faults += 1

   
        steps.append(memory.copy())

    hits = len(reference_string) - page_faults

    return {
        "processId": process_id,
        "pageFaults": page_faults,
        "hits": hits,
        "steps": steps
    }
