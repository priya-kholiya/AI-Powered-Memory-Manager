from queue import Queue

def fifo(process_id, memory_size, reference_string, frames ):
    
    memory_set = set();
    memory_queue = Queue();
    page_faults = 0;
    steps = [];

    for page in reference_string:
         # Page not in memory → page fault

        if page not in memory_set:

             # If memory has space
            if len(memory_set) < frames:
                memory_set.add(page);
                memory_queue.put(page);
            else: 
                # Memory full → remove oldest page
                oldest = memory_queue.get();
                memory_set.remove(oldest);
                memory_set.add(page);
                memory_queue.put(page);
            page_faults+=1

        steps.append(list(memory_queue.queue))

    hits = len(reference_string) - page_faults # pyright: ignore[reportUndefinedVariable]

    return{
        "processId": process_id,
        "pageFaults": page_faults,
        "hits":hits,
        "steps":steps
    }





        



