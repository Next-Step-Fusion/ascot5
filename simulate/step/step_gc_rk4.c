/**
 * @file step_gc_rk4.c
 * @brief Calculate a guiding center step for a struct of particles with RK4
 **/
#include <math.h>
#include "../../ascot5.h"
#include "../../consts.h"
#include "../../B_field.h"
#include "../../E_field.h"
#include "../../math.h"
#include "../../particle.h"
#include "step_gceom.h"
#include "step_gc_rk4.h"

/**
 * @brief Integrate a guiding center step for a struct of particles with RK4
 *
 * This function calculates a guiding center step for a struct of NSIMD 
 * particles with RK4 simultaneously using SIMD instructions. All arrays in the 
 * function are of NSIMD length so vectorization can be performed directly 
 * without gather and scatter operations.
 *
 * @param p simd_gc struct that will be updated
 * @param h pointer to array containing time steps
 * @param Bdata pointer to magnetic field data
 * @param Edata pointer to electric field data
 */
void step_gc_rk4(particle_simd_gc* p, real* h, B_field_data* Bdata, E_field_data* Edata) {

    int i;
    /* Following loop will be executed simultaneously for all i */
    #pragma omp simd aligned(h : 64) simdlen(8)
    for(i = 0; i < NSIMD; i++) {
        if(p->running[i]) {
	    a5err errflag = 0;

            real k1[6];
            real k2[6];
            real k3[6];
            real k4[6];
            real tempy[6];
            real yprev[6];
            real y[6];

            real mass;
            real charge;

            real B_dB[12];
	    real E[3];

	    real R0   = p->r[i];
	    real z0   = p->z[i];

            /* Coordinates are copied from the struct into an array to make 
             * passing parameters easier */
            yprev[0] = p->r[i];
            yprev[1] = p->phi[i];
            yprev[2] = p->z[i];
            yprev[3] = p->vpar[i];
            yprev[4] = p->mu[i];
	    yprev[5] = p->theta[i];
            mass     = p->mass[i];
            charge   = p->charge[i];

	    /* Magnetic field at initial position already known */
	    B_dB[0]  = p->B_r[i];
	    B_dB[1]  = p->B_r_dr[i];
	    B_dB[2]  = p->B_r_dphi[i];
	    B_dB[3]  = p->B_r_dz[i];

	    B_dB[4]  = p->B_phi[i];
	    B_dB[5]  = p->B_phi_dr[i];
	    B_dB[6]  = p->B_phi_dphi[i];
	    B_dB[7]  = p->B_phi_dz[i];

	    B_dB[8]  = p->B_z[i];
	    B_dB[9]  = p->B_z_dr[i];
	    B_dB[10] = p->B_z_dphi[i];
	    B_dB[11] = p->B_z_dz[i];

	    if(!errflag) {errflag = E_field_eval_E(E, yprev[0], yprev[1], yprev[2], Edata, Bdata);}
            if(!errflag) {step_gceom(k1, yprev, mass, charge, B_dB, E);}
            int j;
            /* particle coordinates for the subsequent ydot evaluations are
             * stored in tempy */
            for(j = 0; j < 6; j++) {
                tempy[j] = yprev[j] + h[i]/2.0*k1[j];
            }

            if(!errflag) {errflag = B_field_eval_B_dB(B_dB, tempy[0], tempy[1], tempy[2], Bdata);}
            if(!errflag) {errflag = E_field_eval_E(E, tempy[0], tempy[1], tempy[2], Edata, Bdata);}
            if(!errflag) {step_gceom(k2, tempy, mass, charge, B_dB, E);}
            for(j = 0; j < 6; j++) {
                tempy[j] = yprev[j] + h[i]/2.0*k2[j];
            }

            if(!errflag) {errflag = B_field_eval_B_dB(B_dB, tempy[0], tempy[1], tempy[2], Bdata);}
	    if(!errflag) {errflag = E_field_eval_E(E, tempy[0], tempy[1], tempy[2], Edata, Bdata);}
            if(!errflag) {step_gceom(k3, tempy, mass, charge, B_dB, E);}
            for(j = 0; j < 6; j++) {
                tempy[j] = yprev[j] + h[i]*k3[j];
            }

            if(!errflag) {errflag = B_field_eval_B_dB(B_dB, tempy[0], tempy[1], tempy[2], Bdata);}
	    if(!errflag) {errflag = E_field_eval_E(E, tempy[0], tempy[1], tempy[2], Edata, Bdata);}
            if(!errflag) {step_gceom(k4, tempy, mass, charge, B_dB, E);}
            for(j = 0; j < 6; j++) {
                y[j] = yprev[j]
                    + h[i]/6.0 * (k1[j] + 2*k2[j] + 2*k3[j] + k4[j]);
            } 

	    /* Test that results are physical */
	    if(!errflag && y[0] <= 0)                  {errflag = error_raise(ERR_UNPHYSICAL_GC, __LINE__);}
	    else if(!errflag && fabs(y[4]) >= CONST_C) {errflag = error_raise(ERR_UNPHYSICAL_GC, __LINE__);}
	    else if(!errflag && y[4] < 0)              {errflag = error_raise(ERR_UNPHYSICAL_GC, __LINE__);}

	    /* Update gc phase space position */
	    if(!errflag) {
		p->r[i] = y[0];
		p->phi[i] = y[1];
		p->z[i] = y[2];
		p->vpar[i] = y[3];
		p->mu[i] = y[4];
		p->theta[i] = fmod(y[5],CONST_2PI);
		if(p->theta[i]<0){p->theta[i] = CONST_2PI + p->theta[i];}
	    }

	    /* Evaluate magnetic field (and gradient) and rho at new position */
	    real psi[1];
	    real rho[1];
	    if(!errflag) {errflag = B_field_eval_B_dB(B_dB, p->r[i], p->phi[i], p->z[i], Bdata);}
	    if(!errflag) {errflag = B_field_eval_psi(psi, p->r[i], p->phi[i], p->z[i], Bdata);}
	    if(!errflag) {errflag = B_field_eval_rho(rho, psi[0], Bdata);}

	    if(!errflag) {
		p->B_r[i]        = B_dB[0];
		p->B_r_dr[i]     = B_dB[1];
		p->B_r_dphi[i]   = B_dB[2];
		p->B_r_dz[i]     = B_dB[3];
		
		p->B_phi[i]      = B_dB[4];
		p->B_phi_dr[i]   = B_dB[5];
		p->B_phi_dphi[i] = B_dB[6];
		p->B_phi_dz[i]   = B_dB[7];
		
		p->B_z[i]        = B_dB[8];
		p->B_z_dr[i]     = B_dB[9];
		p->B_z_dphi[i]   = B_dB[10];
		p->B_z_dz[i]     = B_dB[11];
		
		p->rho[i] = rho[0];
		
		
		/* Evaluate pol angle so that it is cumulative */
		real axis_r = B_field_get_axis_r(Bdata);
		real axis_z = B_field_get_axis_z(Bdata);
		p->pol[i] += atan2( (R0-axis_r) * (p->z[i]-axis_z) - (z0-axis_z) * (p->r[i]-axis_r), 
				  (R0-axis_r) * (p->r[i]-axis_r) + (z0-axis_z) * (p->z[i]-axis_z) );
	    }

	    /* Error handling */
	    if(errflag) {
                p->err[i]     = error_module(errflag, ERRMOD_ORBSTEP);
		p->running[i] = 0;
            }
        }
}//printf("%le %le %le %le %le %le %le %le %le %le %le %le\n",B_dB[0][0],B_dB[1][0],B_dB[2][0],B_dB[3][0],B_dB[4][0],B_dB[5][0],B_dB[6][0],B_dB[7][0],B_dB[8][0],B_dB[9][0],B_dB[10][0],B_dB[11][0]);
}


void step_gc_rk4_SIMD(particle_simd_gc* p, real* h, B_field_data* Bdata, E_field_data* Edata) {

    real psi[NSIMD];
    real rho[NSIMD];
    real E[3][NSIMD];
    real B_dB[12][NSIMD];

    int i;
    /* Following loop will be executed simultaneously for all i */
#pragma omp simd  aligned(h : 64) simdlen(8)
    for(i = 0; i < NSIMD; i++) {
        if(p->running[i]) {
	    a5err errflag = 0;

            real k1[6][NSIMD];
            real k2[6][NSIMD];
            real k3[6][NSIMD];
            real k4[6][NSIMD];
            real tempy[6][NSIMD];
            real yprev[6][NSIMD];
            real y[6][NSIMD];

            real mass;
            real charge;


	    real R0   = p->r[i];
	    real z0   = p->z[i];

            /* Coordinates are copied from the struct into an array to make 
             * passing parameters easier */
            yprev[0][i] = p->r[i];
            yprev[1][i] = p->phi[i];
            yprev[2][i] = p->z[i];
            yprev[3][i] = p->vpar[i];
            yprev[4][i] = p->mu[i];
	    yprev[5][i] = p->theta[i];
            mass     = p->mass[i];
            charge   = p->charge[i];

	    /* Magnetic field at initial position already known */
	    B_dB[0][i]  = p->B_r[i];
	    B_dB[1][i]  = p->B_r_dr[i];
	    B_dB[2][i]  = p->B_r_dphi[i];
	    B_dB[3][i]  = p->B_r_dz[i];

	    B_dB[4][i]  = p->B_phi[i];
	    B_dB[5][i]  = p->B_phi_dr[i];
	    B_dB[6][i]  = p->B_phi_dphi[i];
	    B_dB[7][i]  = p->B_phi_dz[i];

	    B_dB[8][i]  = p->B_z[i];
	    B_dB[9][i]  = p->B_z_dr[i];
	    B_dB[10][i] = p->B_z_dphi[i];
	    B_dB[11][i] = p->B_z_dz[i];

	    if(!errflag) {errflag = E_field_eval_E_SIMD(i, E, yprev[0][i], yprev[1][i], yprev[2][i], Edata, Bdata);}
            if(!errflag) {step_gceom_SIMD(i, k1, yprev, mass, charge, B_dB, E);}
            int j;
            /* particle coordinates for the subsequent ydot evaluations are
             * stored in tempy */
            for(j = 0; j < 6; j++) {
                tempy[j][i] = yprev[j][i] + h[i]/2.0*k1[j][i];
            }

            if(!errflag) {errflag = B_field_eval_B_dB_SIMD(i, B_dB, tempy[0][i], tempy[1][i], tempy[2][i], Bdata);}
            if(!errflag) {errflag = E_field_eval_E_SIMD(i, E, tempy[0][i], tempy[1][i], tempy[2][i], Edata, Bdata);}
            if(!errflag) {step_gceom_SIMD(i, k2, tempy, mass, charge, B_dB, E);}
            for(j = 0; j < 6; j++) {
                tempy[j][i] = yprev[j][i] + h[i]/2.0*k2[j][i];
            }

            if(!errflag) {errflag = B_field_eval_B_dB_SIMD(i, B_dB, tempy[0][i], tempy[1][i], tempy[2][i], Bdata);}
	    if(!errflag) {errflag = E_field_eval_E_SIMD(i, E, tempy[0][i], tempy[1][i], tempy[2][i], Edata, Bdata);}
            if(!errflag) {step_gceom_SIMD(i, k3, tempy, mass, charge, B_dB, E);}
            for(j = 0; j < 6; j++) {
                tempy[j][i] = yprev[j][i] + h[i]*k3[j][i];
            }

            if(!errflag) {errflag = B_field_eval_B_dB_SIMD(i, B_dB, tempy[0][i], tempy[1][i], tempy[2][i], Bdata);}
	    if(!errflag) {errflag = E_field_eval_E_SIMD(i, E, tempy[0][i], tempy[1][i], tempy[2][i], Edata, Bdata);}
            if(!errflag) {step_gceom_SIMD(i, k4, tempy, mass, charge, B_dB, E);}
            for(j = 0; j < 6; j++) {
                y[j][i] = yprev[j][i]
                    + h[i]/6.0 * (k1[j][i] + 2*k2[j][i] + 2*k3[j][i] + k4[j][i]);
            } 

	    /* Test that results are physical */
	    if(!errflag && y[0][i] <= 0)                  {errflag = error_raise(ERR_UNPHYSICAL_GC, __LINE__);}
	    else if(!errflag && fabs(y[4][i]) >= CONST_C) {errflag = error_raise(ERR_UNPHYSICAL_GC, __LINE__);}
	    else if(!errflag && y[4][i] < 0)              {errflag = error_raise(ERR_UNPHYSICAL_GC, __LINE__);}

	    /* Update gc phase space position */
	    if(!errflag) {
		p->r[i] = y[0][i];
		p->phi[i] = y[1][i];
		p->z[i] = y[2][i];
		p->vpar[i] = y[3][i];
		p->mu[i] = y[4][i];
		p->theta[i] = fmod(y[5][i],CONST_2PI);
		if(p->theta[i]<0){p->theta[i] = CONST_2PI + p->theta[i];}
	    }

	    /* Evaluate magnetic field (and gradient) and rho at new position */
	    if(!errflag) {errflag = B_field_eval_B_dB_SIMD(i, B_dB, p->r[i], p->phi[i], p->z[i], Bdata);}
	    if(!errflag) {errflag = B_field_eval_psi_SIMD(i, psi, p->r[i], p->phi[i], p->z[i], Bdata);}
	    if(!errflag) {errflag = B_field_eval_rho_SIMD(i, rho, psi[i], Bdata);}

	    if(!errflag) {
		p->B_r[i]        = B_dB[0][i];
		p->B_r_dr[i]     = B_dB[1][i];
		p->B_r_dphi[i]   = B_dB[2][i];
		p->B_r_dz[i]     = B_dB[3][i];
		
		p->B_phi[i]      = B_dB[4][i];
		p->B_phi_dr[i]   = B_dB[5][i];
		p->B_phi_dphi[i] = B_dB[6][i];
		p->B_phi_dz[i]   = B_dB[7][i];
		
		p->B_z[i]        = B_dB[8][i];
		p->B_z_dr[i]     = B_dB[9][i];
		p->B_z_dphi[i]   = B_dB[10][i];
		p->B_z_dz[i]     = B_dB[11][i];
		
		p->rho[i] = rho[i];
		
		
		/* Evaluate pol angle so that it is cumulative */
		real axis_r = B_field_get_axis_r(Bdata);
		real axis_z = B_field_get_axis_z(Bdata);
		p->pol[i] += atan2( (R0-axis_r) * (p->z[i]-axis_z) - (z0-axis_z) * (p->r[i]-axis_r), 
				  (R0-axis_r) * (p->r[i]-axis_r) + (z0-axis_z) * (p->z[i]-axis_z) );
	    }

	    /* Error handling */
	    if(errflag) {
                p->err[i]     = error_module(errflag, ERRMOD_ORBSTEP);
		p->running[i] = 0;
            }
        }
    }
}
