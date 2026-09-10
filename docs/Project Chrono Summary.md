## Project Chrono

Summary of main features: 

**Physics modeling**
- Rigid body support.
- Flexible body support - both for ANCF and co-rotational nonlinear finite element analysis.
- Support for fluid-solid interaction problems, via Chrono::FSI module.
- Coulomb friction model capturing stick-slip phenomena.  
...

**Solver**
- HHT solver for index 3 differential algebraic equations.
- Symplectic first order half-implicit Euler solver for large frictional contact problems.
- Speed-impulse level solver for handling large frictional contact problems.
- Handling of redundant/ill posed constraints.  
...

**Collision detection features**
- Supports compounds of spheres, cubes, convex geometries, triangle meshes, etc.
- Additional collision support provided by the Bullet collision detection engine, which is wrapped inside Chrono.
- Broad phase collision detection: sweep-and-prune SAT.
- Narrow phase collision detection: AABB and/or OBB binary volume trees.  
...

Introductory Page: https://api.projectchrono.org/introduction_chrono.html  


Installation Guide: https://api.projectchrono.org/tutorial_install_chrono.html  