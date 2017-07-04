/**
 * @file simulate_fo_fixed.h
 * @brief Header file for simulate_fo_fixed.c
 */
#ifndef SIMULATE_FO_FIXED_H
#define SIMULATE_FO_FIXED_H

#include "../ascot5.h"
#include "../simulate.h"
#include "../particle.h"

#pragma omp declare target
void simulate_fo_fixed(particle_queue_fo* pq, sim_data* sim);
#pragma omp end declare target

#endif
