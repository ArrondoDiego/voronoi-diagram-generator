# Algorithm VORONOIDIAGRAM( $P$ )

*Input.* A set  $P := \{p_1, \dots, p_n\}$  of point sites in the plane.

*Output.* The Voronoi diagram  $\text{Vor}(P)$  given inside a bounding box in a doubly-connected edge list  $\mathcal{D}$ .

1. Initialize the event queue  $\mathcal{Q}$  with all site events, initialize an empty status structure  $\mathcal{T}$  and an empty doubly-connected edge list  $\mathcal{D}$ .
2. **while**  $\mathcal{Q}$  is not empty
3.     **do** Remove the event with largest  $y$ -coordinate from  $\mathcal{Q}$ .
4.     **if** the event is a site event, occurring at site  $p_i$
5.         **then** HANDLESITEEVENT( $p_i$ )
6.     **else** HANDLECIRCLEEVENT( $\gamma$ ), where  $\gamma$  is the leaf of  $\mathcal{T}$  representing the arc that will disappear
7. The internal nodes still present in  $\mathcal{T}$  correspond to the half-infinite edges of the Voronoi diagram. Compute a bounding box that contains all vertices of the Voronoi diagram in its interior, and attach the half-infinite edges to the bounding box by updating the doubly-connected edge list appropriately.


8. Traverse the half-edges of the doubly-connected edge list to add the cell records and the pointers to and from them.

The procedures to handle the events are defined as follows.

HANDLESITEEVENT( $p_i$ )

1. If  $\mathcal{T}$  is empty, insert  $p_i$  into it (so that  $\mathcal{T}$  consists of a single leaf storing  $p_i$ ) and return. Otherwise, continue with steps 2–5.
2. Search in  $\mathcal{T}$  for the arc  $\alpha$  vertically above  $p_i$ . If the leaf representing  $\alpha$  has a pointer to a circle event in  $\Omega$ , then this circle event is a false alarm and it must be deleted from  $\Omega$ .
3. Replace the leaf of  $\mathcal{T}$  that represents  $\alpha$  with a subtree having three leaves. The middle leaf stores the new site  $p_i$  and the other two leaves store the site  $p_j$  that was originally stored with  $\alpha$ . Store the tuples  $\langle p_j, p_i \rangle$  and  $\langle p_i, p_j \rangle$  representing the new breakpoints at the two new internal nodes. Perform rebalancing operations on  $\mathcal{T}$  if necessary.
4. Create new half-edge records in the Voronoi diagram structure for the edge separating  $\mathcal{V}(p_i)$  and  $\mathcal{V}(p_j)$ , which will be traced out by the two new breakpoints.
5. Check the triple of consecutive arcs where the new arc for  $p_i$  is the left arc to see if the breakpoints converge. If so, insert the circle event into  $\Omega$  and add pointers between the node in  $\mathcal{T}$  and the node in  $\Omega$ . Do the same for the triple where the new arc is the right arc.

HANDLECIRCLEEVENT( $\gamma$ )

1. Delete the leaf  $\gamma$  that represents the disappearing arc  $\alpha$  from  $\mathcal{T}$ . Update the tuples representing the breakpoints at the internal nodes. Perform rebalancing operations on  $\mathcal{T}$  if necessary. Delete all circle events involving  $\alpha$  from  $\Omega$ ; these can be found using the pointers from the predecessor and the successor of  $\gamma$  in  $\mathcal{T}$ . (The circle event where  $\alpha$  is the middle arc is currently being handled, and has already been deleted from  $\Omega$ .)
2. Add the center of the circle causing the event as a vertex record to the doubly-connected edge list  $\mathcal{D}$  storing the Voronoi diagram under construction. Create two half-edge records corresponding to the new breakpoint of the beach line. Set the pointers between them appropriately. Attach the three new records to the half-edge records that end at the vertex.
3. Check the new triple of consecutive arcs that has the former left neighbor of  $\alpha$  as its middle arc to see if the two breakpoints of the triple converge. If so, insert the corresponding circle event into  $\Omega$ , and set pointers between the new circle event in  $\Omega$  and the corresponding leaf of  $\mathcal{T}$ . Do the same for the triple where the former right neighbor is the middle arc.
