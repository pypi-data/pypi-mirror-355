* (Jiahang) This folder is a manually revised version of the same name folder. This folder contains updates from more than just 19/04/25.
# updates
## 19/04/25
* differentiate "optional" edges from "mandatory" edges using dashed lines.
* add destination arrow.
* put consumed products in edges.

## 20/04/05
* add relevant downstream arguments into edges
* add customized API node only to dependency graph which 1) have arguments w/o default values, and 2) arguments cannot be satisified by any upstream API. 
  * If argument w/o default values can be satisfied by a upstream API, then we save user's efforts to let him select one upstream API
  * If not, we let user input their own index.
* 