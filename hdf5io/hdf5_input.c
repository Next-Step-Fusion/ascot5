#include "../simulate.h"
#include "hdf5.h"
#include "hdf5_helpers.h"
#include "hdf5_hl.h"
#include "hdf5_input.h"
#include "hdf5_simulate.h"
#include "hdf5_bfield.h"
#include "hdf5_plasma.h"
#include "hdf5_efield.h"
#include "hdf5_wall.h"
#include "hdf5_markers.h"

int hdf5_input(sim_offload_data* sim, 
	       real** B_offload_array,
	       real** E_offload_array,
	       real** plasma_offload_array,
	       real** wall_offload_array,
               input_particle* p,
               int* n_markers){
    
    /* This init disables automatic error messages.
     * We want to generate our own that are more informative.*/
    hdf5_init();

    /* Check if requested hdf5 exists and open it */
    hid_t f = hdf5_open(sim->hdf5fn);
    if(f < 0) {
	printf("\nError: Attempted to access %s.\n",sim->hdf5fn);
	printf("File not found.\n");
	return -1;
    }

    /* Check that input contains all relevant groups */
    herr_t err;
    err = hdf5_find_group(f, "/options/");
    if(err < 0) {
	printf("\nError: Options not found within %s.\n",sim->hdf5fn);
	return -1;
    }

    err = hdf5_find_group(f, "/bfield/");
    if(err < 0) {
	printf("\nError: Magnetic field not found within %s.\n",sim->hdf5fn);
	return -1;
    }

    err = hdf5_find_group(f, "/efield/");
    if(err < 0) {
	printf("\nError: Electric field not found within %s.\n",sim->hdf5fn);
	return -1;
    }

    err = hdf5_find_group(f, "/plasma/");
    if(err < 0) {
	printf("\nError: Plasma not found within %s.\n",sim->hdf5fn);
	return -1;
    }

    err = hdf5_find_group(f, "/wall/");
    if(err < 0) {
	printf("\nError: Wall not found within %s.\n",sim->hdf5fn);
	return -1;
    }

    err = hdf5_find_group(f, "/markers/");
    if(err < 0) {
	printf("\nError: Markers not found within %s.\n",sim->hdf5fn);
	return -1;
    }

    /* Read input from hdf5 and initialize */
    hdf5_simulate(f, sim);
    if(err < 0) {
	printf("\nError: Failed to initialize options from %s.\n",sim->hdf5fn);
	return -1;
    }

    hdf5_bfield_init_offload(f,&(sim->B_offload_data), B_offload_array);
    if(err < 0) {
	printf("\nError: Failed to initialize magnetic field from %s.\n",sim->hdf5fn);
	return -1;
    }

    hdf5_efield_init_offload(f,&(sim->E_offload_data), E_offload_array);
    if(err < 0) {
	printf("\nError: Failed to initialize electric field from %s.\n",sim->hdf5fn);
	return -1;
    }

    hdf5_plasma_init_offload(f,&(sim->plasma_offload_data), plasma_offload_array);
    if(err < 0) {
	printf("\nError: Failed to initialize plasma from %s.\n",sim->hdf5fn);
	return -1;
    }

    hdf5_wall_init_offload(f,&(sim->wall_offload_data), wall_offload_array);
    if(err < 0) {
	printf("\nError: Failed to initialize wall from %s.\n",sim->hdf5fn);
	return -1;
    }

    hdf5_markers_init(f, n_markers, p);
    if(err < 0) {
	printf("\nError: Failed to initialize markers from %s.\n",sim->hdf5fn);
	return -1;
    }
	
    /* Close the hdf5 file */
    err = hdf5_close(f);
    if(err < 0) {
	printf("\nError: Could not close hdf5 file %s.\n",sim->hdf5fn);
	return -1;
    }

    return 0;
}
