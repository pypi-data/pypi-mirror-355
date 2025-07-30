/*      Compiler: ECL 24.5.10                                         */
/*      Date: 2025/6/15 23:13 (yyyy/mm/dd)                            */
/*      Machine: Darwin 23.6.0 arm64                                  */
/*      Source: /Users/runner/sage-local/var/tmp/sage/build/fricas-1.3.12/src/pre-generated/src/algebra/CDFMAT.lsp */
#include <ecl/ecl-cmp.h>
#include "/Users/runner/sage-local/var/tmp/sage/build/fricas-1.3.12/src/_build/target/aarch64-apple-darwin23.6.0/algebra/CDFMAT.eclh"
/*      function definition for CDFMAT;minRowIndex;%I;1               */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L789_cdfmat_minrowindex__i_1_(cl_object v1_x_, cl_object v2_)
{
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 value0 = ecl_make_fixnum(0);
 cl_env_copy->nvalues = 1;
 return value0;
}
/*      function definition for CDFMAT;minColIndex;%I;2               */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L790_cdfmat_mincolindex__i_2_(cl_object v1_x_, cl_object v2_)
{
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 value0 = ecl_make_fixnum(0);
 cl_env_copy->nvalues = 1;
 return value0;
}
/*      function definition for CDFMAT;nrows;%Nni;3                   */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L791_cdfmat_nrows__nni_3_(cl_object v1_x_, cl_object v2_)
{
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 value0 = ecl_make_fixnum(ecl_array_dimension(v1_x_,0));
 cl_env_copy->nvalues = 1;
 return value0;
}
/*      function definition for CDFMAT;ncols;%Nni;4                   */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L792_cdfmat_ncols__nni_4_(cl_object v1_x_, cl_object v2_)
{
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_fixnum v3;
  v3 = ecl_array_dimension(v1_x_,1);
  value0 = ecl_truncate2(ecl_make_fixnum(v3),ecl_make_fixnum(2));
  return value0;
 }
}
/*      function definition for CDFMAT;maxRowIndex;%I;5               */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L793_cdfmat_maxrowindex__i_5_(cl_object v1_x_, cl_object v2_)
{
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_fixnum v3;
  v3 = ecl_array_dimension(v1_x_,0);
  value0 = ecl_minus(ecl_make_fixnum(v3),ecl_make_fixnum(1));
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for CDFMAT;maxColIndex;%I;6               */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L794_cdfmat_maxcolindex__i_6_(cl_object v1_x_, cl_object v2_)
{
 cl_object T0;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_fixnum v3;
  v3 = ecl_array_dimension(v1_x_,1);
  T0 = ecl_truncate2(ecl_make_fixnum(v3),ecl_make_fixnum(2));
  value0 = ecl_minus(T0,ecl_make_fixnum(1));
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for CDFMAT;qelt;%2IC;7                    */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L795_cdfmat_qelt__2ic_7_(cl_object v1_m_, cl_object v2_i_, cl_object v3_j_, cl_object v4_)
{
 cl_object T0, T1;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  double v5;
  {
   cl_object v6;
   v6 = v1_m_;
   T0 = v6;
   {
    cl_fixnum v7;
    {
     cl_fixnum v8dim13;
     cl_fixnum v9;
     v8dim13 = (v6)->array.dims[1];
     v9 = 0;
     v9 = (v9)+(ecl_fixnum(v2_i_));
     v9 = (v9)*(v8dim13);
     {
      cl_fixnum v10;
      v10 = ecl_fixnum(ecl_times(ecl_make_fixnum(2),v3_j_));
      v9 = (v9)+(v10);
     }
     v7 = v9;
    }
    v5 = (T0)->array.self.df[v7];
   }
  }
  {
   double v6;
   {
    cl_object v7;
    v7 = v1_m_;
    T0 = v7;
    {
     cl_fixnum v8;
     {
      cl_fixnum v9dim15;
      cl_fixnum v10;
      v9dim15 = (v7)->array.dims[1];
      v10 = 0;
      v10 = (v10)+(ecl_fixnum(v2_i_));
      v10 = (v10)*(v9dim15);
      {
       cl_fixnum v11;
       T1 = ecl_times(ecl_make_fixnum(2),v3_j_);
       v11 = ecl_fixnum(ecl_plus(T1,ecl_make_fixnum(1)));
       v10 = (v10)+(v11);
      }
      v8 = v10;
     }
     v6 = (T0)->array.self.df[v8];
    }
   }
   value0 = CONS(ecl_make_double_float(v5),ecl_make_double_float(v6));
   cl_env_copy->nvalues = 1;
   return value0;
  }
 }
}
/*      function definition for CDFMAT;elt;%2IC;8                     */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L796_cdfmat_elt__2ic_8_(cl_object v1_m_, cl_object v2_i_, cl_object v3_j_, cl_object v4_)
{
 cl_object T0, T1;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  double v5;
  {
   cl_object v6;
   v6 = v1_m_;
   T0 = v6;
   {
    cl_fixnum v7;
    {
     cl_fixnum v8dim17;
     cl_fixnum v9;
     v8dim17 = (v6)->array.dims[1];
     v9 = 0;
     v9 = (v9)+(ecl_fixnum(v2_i_));
     v9 = (v9)*(v8dim17);
     {
      cl_fixnum v10;
      v10 = ecl_fixnum(ecl_times(ecl_make_fixnum(2),v3_j_));
      v9 = (v9)+(v10);
     }
     v7 = v9;
    }
    v5 = (T0)->array.self.df[v7];
   }
  }
  {
   double v6;
   {
    cl_object v7;
    v7 = v1_m_;
    T0 = v7;
    {
     cl_fixnum v8;
     {
      cl_fixnum v9dim19;
      cl_fixnum v10;
      v9dim19 = (v7)->array.dims[1];
      v10 = 0;
      v10 = (v10)+(ecl_fixnum(v2_i_));
      v10 = (v10)*(v9dim19);
      {
       cl_fixnum v11;
       T1 = ecl_times(ecl_make_fixnum(2),v3_j_);
       v11 = ecl_fixnum(ecl_plus(T1,ecl_make_fixnum(1)));
       v10 = (v10)+(v11);
      }
      v8 = v10;
     }
     v6 = (T0)->array.self.df[v8];
    }
   }
   value0 = CONS(ecl_make_double_float(v5),ecl_make_double_float(v6));
   cl_env_copy->nvalues = 1;
   return value0;
  }
 }
}
/*      function definition for CDFMAT;qsetelt!;%2I2C;9               */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L797_cdfmat_qsetelt___2i2c_9_(cl_object v1_m_, cl_object v2_i_, cl_object v3_j_, cl_object v4_r_, cl_object v5_)
{
 cl_object T0, T1;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v6;
  v6 = v1_m_;
  T0 = v6;
  {
   cl_fixnum v7;
   {
    cl_fixnum v8dim21;
    cl_fixnum v9;
    v8dim21 = (v6)->array.dims[1];
    v9 = 0;
    v9 = (v9)+(ecl_fixnum(v2_i_));
    v9 = (v9)*(v8dim21);
    {
     cl_fixnum v10;
     v10 = ecl_fixnum(ecl_times(ecl_make_fixnum(2),v3_j_));
     v9 = (v9)+(v10);
    }
    v7 = v9;
   }
   T1 = _ecl_car(v4_r_);
   (T0)->array.self.df[v7]= ecl_double_float(T1);
  }
 }
 {
  cl_object v6;
  v6 = v1_m_;
  T0 = v6;
  {
   cl_fixnum v7;
   {
    cl_fixnum v8dim23;
    cl_fixnum v9;
    v8dim23 = (v6)->array.dims[1];
    v9 = 0;
    v9 = (v9)+(ecl_fixnum(v2_i_));
    v9 = (v9)*(v8dim23);
    {
     cl_fixnum v10;
     T1 = ecl_times(ecl_make_fixnum(2),v3_j_);
     v10 = ecl_fixnum(ecl_plus(T1,ecl_make_fixnum(1)));
     v9 = (v9)+(v10);
    }
    v7 = v9;
   }
   T1 = _ecl_cdr(v4_r_);
   (T0)->array.self.df[v7]= ecl_double_float(T1);
  }
 }
 value0 = v4_r_;
 cl_env_copy->nvalues = 1;
 return value0;
}
/*      function definition for CDFMAT;setelt!;%2I2C;10               */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L798_cdfmat_setelt___2i2c_10_(cl_object v1_m_, cl_object v2_i_, cl_object v3_j_, cl_object v4_r_, cl_object v5_)
{
 cl_object T0, T1;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v6;
  v6 = v1_m_;
  T0 = v6;
  {
   cl_fixnum v7;
   {
    cl_fixnum v8dim25;
    cl_fixnum v9;
    v8dim25 = (v6)->array.dims[1];
    v9 = 0;
    v9 = (v9)+(ecl_fixnum(v2_i_));
    v9 = (v9)*(v8dim25);
    {
     cl_fixnum v10;
     v10 = ecl_fixnum(ecl_times(ecl_make_fixnum(2),v3_j_));
     v9 = (v9)+(v10);
    }
    v7 = v9;
   }
   T1 = _ecl_car(v4_r_);
   (T0)->array.self.df[v7]= ecl_double_float(T1);
  }
 }
 {
  cl_object v6;
  v6 = v1_m_;
  T0 = v6;
  {
   cl_fixnum v7;
   {
    cl_fixnum v8dim27;
    cl_fixnum v9;
    v8dim27 = (v6)->array.dims[1];
    v9 = 0;
    v9 = (v9)+(ecl_fixnum(v2_i_));
    v9 = (v9)*(v8dim27);
    {
     cl_fixnum v10;
     T1 = ecl_times(ecl_make_fixnum(2),v3_j_);
     v10 = ecl_fixnum(ecl_plus(T1,ecl_make_fixnum(1)));
     v9 = (v9)+(v10);
    }
    v7 = v9;
   }
   T1 = _ecl_cdr(v4_r_);
   (T0)->array.self.df[v7]= ecl_double_float(T1);
  }
 }
 value0 = v4_r_;
 cl_env_copy->nvalues = 1;
 return value0;
}
/*      function definition for CDFMAT;empty;%;11                     */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L799_cdfmat_empty___11_(cl_object v1_)
{
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v2;
  v2 = cl_list(2, ecl_make_fixnum(0), ecl_make_fixnum(0));
  value0 = si_make_pure_array(ECL_SYM("DOUBLE-FLOAT",317), v2, ECL_NIL, ECL_NIL, ECL_NIL, ecl_make_fixnum(0));
  return value0;
 }
}
/*      function definition for CDFMAT;qnew;2Nni%;12                  */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L800_cdfmat_qnew_2nni__12_(cl_object v1_rows_, cl_object v2_cols_, cl_object v3_)
{
 cl_object T0;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v4;
  T0 = ecl_times(ecl_make_fixnum(2),v2_cols_);
  v4 = cl_list(2, v1_rows_, T0);
  value0 = si_make_pure_array(ECL_SYM("DOUBLE-FLOAT",317), v4, ECL_NIL, ECL_NIL, ECL_NIL, ecl_make_fixnum(0));
  return value0;
 }
}
/*      function definition for CDFMAT;new;2NniC%;13                  */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L801_cdfmat_new_2nnic__13_(cl_object v1_rows_, cl_object v2_cols_, cl_object v3_a_, cl_object v4_)
{
 cl_object T0, T1;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v5;
  cl_object v6_j_;
  cl_object v7;
  cl_object v8_i_;
  cl_object v9_res_;
  v5 = ECL_NIL;
  v6_j_ = ECL_NIL;
  v7 = ECL_NIL;
  v8_i_ = ECL_NIL;
  v9_res_ = ECL_NIL;
  {
   cl_object v10;
   T0 = ecl_times(ecl_make_fixnum(2),v2_cols_);
   v10 = cl_list(2, v1_rows_, T0);
   v9_res_ = si_make_pure_array(ECL_SYM("DOUBLE-FLOAT",317), v10, ECL_NIL, ECL_NIL, ECL_NIL, ecl_make_fixnum(0));
  }
  v8_i_ = ecl_make_fixnum(0);
  v7 = ecl_minus(v1_rows_,ecl_make_fixnum(1));
L10:;
  if (!((ecl_fixnum(v8_i_))>(ecl_fixnum(v7)))) { goto L16; }
  goto L11;
L16:;
  v6_j_ = ecl_make_fixnum(0);
  v5 = ecl_minus(v2_cols_,ecl_make_fixnum(1));
L20:;
  if (!((ecl_fixnum(v6_j_))>(ecl_fixnum(v5)))) { goto L26; }
  goto L21;
L26:;
  {
   cl_object v10;
   v10 = v9_res_;
   T0 = v10;
   {
    cl_fixnum v11;
    {
     cl_fixnum v12dim29;
     cl_fixnum v13;
     v12dim29 = (v10)->array.dims[1];
     v13 = 0;
     v13 = (v13)+(ecl_fixnum(v8_i_));
     v13 = (v13)*(v12dim29);
     {
      cl_fixnum v14;
      v14 = ecl_fixnum(ecl_times(ecl_make_fixnum(2),v6_j_));
      v13 = (v13)+(v14);
     }
     v11 = v13;
    }
    T1 = _ecl_car(v3_a_);
    (T0)->array.self.df[v11]= ecl_double_float(T1);
   }
  }
  {
   cl_object v10;
   v10 = v9_res_;
   T0 = v10;
   {
    cl_fixnum v11;
    {
     cl_fixnum v12dim31;
     cl_fixnum v13;
     v12dim31 = (v10)->array.dims[1];
     v13 = 0;
     v13 = (v13)+(ecl_fixnum(v8_i_));
     v13 = (v13)*(v12dim31);
     {
      cl_fixnum v14;
      T1 = ecl_times(ecl_make_fixnum(2),v6_j_);
      v14 = ecl_fixnum(ecl_plus(T1,ecl_make_fixnum(1)));
      v13 = (v13)+(v14);
     }
     v11 = v13;
    }
    T1 = _ecl_cdr(v3_a_);
    (T0)->array.self.df[v11]= ecl_double_float(T1);
   }
  }
  goto L28;
L28:;
  v6_j_ = ecl_make_fixnum((ecl_fixnum(v6_j_))+1);
  goto L20;
L21:;
  goto L18;
L18:;
  v8_i_ = ecl_make_fixnum((ecl_fixnum(v8_i_))+1);
  goto L10;
L11:;
  goto L9;
L9:;
  value0 = v9_res_;
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for ComplexDoubleFloatMatrix;             */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L802_complexdoublefloatmatrix__()
{
 cl_object T0, T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13, T14, T15, T16, T17, T18, T19, T20, T21, T22, T23, T24, T25, T26, T27, T28, T29, T30, T31, T32, T33, T34, T35;
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 {
  cl_object v1_dv__;
  cl_object v2_;
  cl_object v3;
  cl_object v4;
  cl_object v5;
  cl_object v6_pv__;
  v1_dv__ = ECL_NIL;
  v2_ = ECL_NIL;
  v3 = ECL_NIL;
  v4 = ECL_NIL;
  v5 = ECL_NIL;
  v6_pv__ = ECL_NIL;
  v1_dv__ = VV[20];
  v2_ = ecl_function_dispatch(cl_env_copy,VV[55])(1, ecl_make_fixnum(49)) /*  GETREFV */;
  (v2_)->vector.self.t[0]= v1_dv__;
  T0 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat   */;
  T1 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T0) /*  Complex   */;
  T2 = ecl_function_dispatch(cl_env_copy,VV[58])(2, T1, VV[21]) /*  HasCategory */;
  T3 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat   */;
  T4 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T3) /*  Complex   */;
  T5 = ecl_function_dispatch(cl_env_copy,VV[58])(2, T4, VV[22]) /*  HasCategory */;
  T6 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat   */;
  T7 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T6) /*  Complex   */;
  T8 = ecl_function_dispatch(cl_env_copy,VV[58])(2, T7, VV[23]) /*  HasCategory */;
  T9 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat   */;
  T10 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T9) /*  Complex  */;
  T11 = ecl_function_dispatch(cl_env_copy,VV[58])(2, T10, VV[24]) /*  HasCategory */;
  T12 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat  */;
  T13 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T12) /*  Complex */;
  v3 = ecl_function_dispatch(cl_env_copy,VV[58])(2, T13, VV[25]) /*  HasCategory */;
  T13 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat  */;
  T14 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T13) /*  Complex */;
  value0 = ecl_function_dispatch(cl_env_copy,VV[58])(2, T14, VV[21]) /*  HasCategory */;
  if ((value0)!=ECL_NIL) { goto L17; }
  T12 = v3;
  goto L15;
L17:;
  T12 = value0;
  goto L15;
L15:;
  T14 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat  */;
  T15 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T14) /*  Complex */;
  value0 = ecl_function_dispatch(cl_env_copy,VV[58])(2, T15, VV[24]) /*  HasCategory */;
  if ((value0)!=ECL_NIL) { goto L21; }
  T14 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat  */;
  T15 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T14) /*  Complex */;
  value0 = ecl_function_dispatch(cl_env_copy,VV[58])(2, T15, VV[21]) /*  HasCategory */;
  if ((value0)!=ECL_NIL) { goto L21; }
  T14 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat  */;
  T15 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T14) /*  Complex */;
  value0 = ecl_function_dispatch(cl_env_copy,VV[58])(2, T15, VV[22]) /*  HasCategory */;
  if ((value0)!=ECL_NIL) { goto L21; }
  T13 = v3;
  goto L19;
L21:;
  T13 = value0;
  goto L19;
L19:;
  T14 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat  */;
  T15 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T14) /*  Complex */;
  if (Null(ecl_function_dispatch(cl_env_copy,VV[58])(2, T15, VV[26]) /*  HasCategory */)) { goto L27; }
  T14 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat  */;
  T15 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T14) /*  Complex */;
  v4 = ecl_function_dispatch(cl_env_copy,VV[58])(2, T15, VV[25]) /*  HasCategory */;
  goto L25;
L27:;
  v4 = ECL_NIL;
  goto L25;
L25:;
  T15 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat  */;
  T16 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T15) /*  Complex */;
  if (Null(ecl_function_dispatch(cl_env_copy,VV[58])(2, T16, VV[26]) /*  HasCategory */)) { goto L34; }
  T15 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat  */;
  T16 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T15) /*  Complex */;
  value0 = ecl_function_dispatch(cl_env_copy,VV[58])(2, T16, VV[21]) /*  HasCategory */;
  goto L32;
L34:;
  value0 = ECL_NIL;
  goto L32;
L32:;
  if ((value0)!=ECL_NIL) { goto L31; }
  T14 = v4;
  goto L29;
L31:;
  T14 = value0;
  goto L29;
L29:;
  T15 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat  */;
  T16 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T15) /*  Complex */;
  v5 = ecl_function_dispatch(cl_env_copy,VV[58])(2, T16, VV[27]) /*  HasCategory */;
  value0 = v5;
  if ((value0)!=ECL_NIL) { goto L39; }
  T15 = v4;
  goto L37;
L39:;
  T15 = value0;
  goto L37;
L37:;
  T16 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat  */;
  T17 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T16) /*  Complex */;
  T18 = ecl_function_dispatch(cl_env_copy,VV[58])(2, T17, VV[28]) /*  HasCategory */;
  T19 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat  */;
  T20 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T19) /*  Complex */;
  T21 = ecl_function_dispatch(cl_env_copy,VV[58])(2, T20, VV[29]) /*  HasCategory */;
  T23 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat  */;
  T24 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T23) /*  Complex */;
  if (Null(ecl_function_dispatch(cl_env_copy,VV[58])(2, T24, VV[30]) /*  HasCategory */)) { goto L43; }
  T23 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat  */;
  T24 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T23) /*  Complex */;
  T22 = ecl_function_dispatch(cl_env_copy,VV[58])(2, T24, VV[29]) /*  HasCategory */;
  goto L41;
L43:;
  T22 = ECL_NIL;
  goto L41;
L41:;
  T23 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat  */;
  T24 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T23) /*  Complex */;
  T25 = ecl_function_dispatch(cl_env_copy,VV[58])(2, T24, VV[31]) /*  HasCategory */;
  T26 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat  */;
  T27 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T26) /*  Complex */;
  T28 = ecl_function_dispatch(cl_env_copy,VV[58])(2, T27, VV[32]) /*  HasCategory */;
  T29 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat  */;
  T30 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T29) /*  Complex */;
  T31 = ecl_function_dispatch(cl_env_copy,VV[58])(2, T30, VV[33]) /*  HasCategory */;
  T32 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat  */;
  T33 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T32) /*  Complex */;
  T34 = ecl_function_dispatch(cl_env_copy,VV[58])(2, T33, VV[34]) /*  HasCategory */;
  T35 = cl_list(18, T2, T5, T8, T11, v3, T12, T13, v4, T14, v5, T15, T18, T21, T22, T25, T28, T31, T34);
  v6_pv__ = ecl_function_dispatch(cl_env_copy,VV[59])(3, ecl_make_fixnum(0), ecl_make_fixnum(0), T35) /*  buildPredVector */;
  (v2_)->vector.self.t[3]= v6_pv__;
  T0 = CONS(ecl_make_fixnum(1),v2_);
  ecl_function_dispatch(cl_env_copy,VV[60])(4, ECL_SYM_VAL(cl_env_copy,VV[35]), VV[36], ECL_NIL, T0) /*  haddProp */;
  ecl_function_dispatch(cl_env_copy,VV[61])(1, v2_) /*  stuffDomainSlots */;
  if (Null(ecl_function_dispatch(cl_env_copy,VV[58])(2, v2_, VV[37]) /*  HasCategory */)) { goto L49; }
  ecl_function_dispatch(cl_env_copy,VV[62])(2, v2_, ecl_make_fixnum(262144)) /*  augmentPredVector */;
  goto L47;
L49:;
  goto L47;
L47:;
  if (Null(ecl_function_dispatch(cl_env_copy,VV[58])(2, v2_, VV[37]) /*  HasCategory */)) { goto L53; }
  T0 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat   */;
  T1 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T0) /*  Complex   */;
  if (Null(ecl_function_dispatch(cl_env_copy,VV[58])(2, T1, VV[23]) /*  HasCategory */)) { goto L53; }
  ecl_function_dispatch(cl_env_copy,VV[62])(2, v2_, ecl_make_fixnum(524288)) /*  augmentPredVector */;
  goto L51;
L53:;
  goto L51;
L51:;
  if (Null(ecl_function_dispatch(cl_env_copy,VV[58])(2, v2_, VV[37]) /*  HasCategory */)) { goto L58; }
  T0 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat   */;
  T1 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T0) /*  Complex   */;
  if (Null(ecl_function_dispatch(cl_env_copy,VV[58])(2, T1, VV[24]) /*  HasCategory */)) { goto L58; }
  ecl_function_dispatch(cl_env_copy,VV[62])(2, v2_, ecl_make_fixnum(1048576)) /*  augmentPredVector */;
  goto L56;
L58:;
  goto L56;
L56:;
  if (Null(ecl_function_dispatch(cl_env_copy,VV[58])(2, v2_, VV[37]) /*  HasCategory */)) { goto L68; }
  T0 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat   */;
  T1 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T0) /*  Complex   */;
  if ((ecl_function_dispatch(cl_env_copy,VV[58])(2, T1, VV[24]) /*  HasCategory */)!=ECL_NIL) { goto L65; }
  goto L66;
L68:;
  goto L66;
L66:;
  T0 = ecl_function_dispatch(cl_env_copy,VV[56])(0) /*  DoubleFloat   */;
  T1 = ecl_function_dispatch(cl_env_copy,VV[57])(1, T0) /*  Complex   */;
  if ((ecl_function_dispatch(cl_env_copy,VV[58])(2, T1, VV[22]) /*  HasCategory */)!=ECL_NIL) { goto L65; }
  if (Null(v3)) { goto L63; }
  goto L64;
L65:;
L64:;
  ecl_function_dispatch(cl_env_copy,VV[62])(2, v2_, ecl_make_fixnum(2097152)) /*  augmentPredVector */;
  goto L61;
L63:;
  goto L61;
L61:;
  v6_pv__ = (v2_)->vector.self.t[3];
  value0 = v2_;
  cl_env_copy->nvalues = 1;
  return value0;
 }
}
/*      function definition for ComplexDoubleFloatMatrix              */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L803_complexdoublefloatmatrix_()
{
 cl_object T0, T1, T2, T3, T4;
 cl_object volatile env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object volatile value0;
TTL:
 {
  volatile cl_object v1;
  v1 = ECL_NIL;
  v1 = ecl_gethash_safe(VV[36],ECL_SYM_VAL(cl_env_copy,VV[35]),ECL_NIL);
  if (Null(v1)) { goto L3; }
  T0 = _ecl_cdar(v1);
  value0 = ecl_function_dispatch(cl_env_copy,VV[64])(1, T0) /*  CDRwithIncrement */;
  return value0;
L3:;
  {
   volatile bool unwinding = FALSE;
   cl_index v2=ECL_STACK_INDEX(cl_env_copy),v3;
   ecl_frame_ptr next_fr;
   ecl_frs_push(cl_env_copy,ECL_PROTECT_TAG);
   if (__ecl_frs_push_result) {
     unwinding = TRUE; next_fr=cl_env_copy->nlj_fr;
   } else {
   {
    cl_object v4;
    T0 = ECL_SYM_VAL(cl_env_copy,VV[35]);
    T1 = ecl_function_dispatch(cl_env_copy,VV[19])(0) /*  ComplexDoubleFloatMatrix; */;
    T2 = cl_listX(3, ECL_NIL, ecl_make_fixnum(1), T1);
    T3 = ecl_list1(T2);
    T4 = si_hash_set(VV[36], T0, T3);
    v4 = _ecl_cddar(T4);
    v1 = ECL_T;
    cl_env_copy->values[0] = v4;
    cl_env_copy->nvalues = 1;
   }
   }
   ecl_frs_pop(cl_env_copy);
   v3=ecl_stack_push_values(cl_env_copy);
   if ((v1)!=ECL_NIL) { goto L10; }
   cl_remhash(VV[36], ECL_SYM_VAL(cl_env_copy,VV[35]));
L10:;
   ecl_stack_pop_values(cl_env_copy,v3);
   if (unwinding) ecl_unwind(cl_env_copy,next_fr);
   ECL_STACK_SET_INDEX(cl_env_copy,v2);
   return cl_env_copy->values[0];
  }
 }
}

#include "/Users/runner/sage-local/var/tmp/sage/build/fricas-1.3.12/src/_build/target/aarch64-apple-darwin23.6.0/algebra/CDFMAT.data"
#ifdef __cplusplus
extern "C"
#endif
ECL_DLLEXPORT void init_fas_CODE(cl_object flag)
{
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
 cl_object *VVtemp;
 if (flag != OBJNULL){
 Cblock = flag;
 #ifndef ECL_DYNAMIC_VV
 flag->cblock.data = VV;
 #endif
 flag->cblock.data_size = VM;
 flag->cblock.temp_data_size = VMtemp;
 flag->cblock.data_text = compiler_data_text;
 flag->cblock.cfuns_size = compiler_cfuns_size;
 flag->cblock.cfuns = compiler_cfuns;
 flag->cblock.source = ecl_make_constant_base_string("/Users/runner/sage-local/var/tmp/sage/build/fricas-1.3.12/src/pre-generated/src/algebra/CDFMAT.lsp",-1);
 return;}
 #ifdef ECL_DYNAMIC_VV
 VV = Cblock->cblock.data;
 #endif
 Cblock->cblock.data_text = (const cl_object *)"@EcLtAg:init_fas_CODE@";
 VVtemp = Cblock->cblock.temp_data;
 ECL_DEFINE_SETF_FUNCTIONS
  ecl_function_dispatch(cl_env_copy,VV[40])(3, VV[0], VV[1], VVtemp[0]) /*  PUT */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[0], ECL_SYM("LOCATION",1862), VVtemp[1], VVtemp[2]) /*  ANNOTATE */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[0], ECL_SYM("LAMBDA-LIST",1000), ECL_NIL, VVtemp[3]) /*  ANNOTATE */;
  ecl_cmp_defun(VV[41]);                          /*  CDFMAT;minRowIndex;%I;1 */
  ecl_function_dispatch(cl_env_copy,VV[40])(3, VV[2], VV[1], VVtemp[0]) /*  PUT */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[2], ECL_SYM("LOCATION",1862), VVtemp[4], VVtemp[5]) /*  ANNOTATE */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[2], ECL_SYM("LAMBDA-LIST",1000), ECL_NIL, VVtemp[3]) /*  ANNOTATE */;
  ecl_cmp_defun(VV[42]);                          /*  CDFMAT;minColIndex;%I;2 */
  ecl_function_dispatch(cl_env_copy,VV[40])(3, VV[3], VV[1], VV[4]) /*  PUT */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[3], ECL_SYM("LOCATION",1862), VVtemp[6], VVtemp[7]) /*  ANNOTATE */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[3], ECL_SYM("LAMBDA-LIST",1000), ECL_NIL, VVtemp[3]) /*  ANNOTATE */;
  ecl_cmp_defun(VV[43]);                          /*  CDFMAT;nrows;%Nni;3 */
  ecl_function_dispatch(cl_env_copy,VV[40])(3, VV[5], VV[1], VV[6]) /*  PUT */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[5], ECL_SYM("LOCATION",1862), VVtemp[8], VVtemp[9]) /*  ANNOTATE */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[5], ECL_SYM("LAMBDA-LIST",1000), ECL_NIL, VVtemp[3]) /*  ANNOTATE */;
  ecl_cmp_defun(VV[44]);                          /*  CDFMAT;ncols;%Nni;4 */
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[7], ECL_SYM("LOCATION",1862), VVtemp[10], VVtemp[11]) /*  ANNOTATE */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[7], ECL_SYM("LAMBDA-LIST",1000), ECL_NIL, VVtemp[3]) /*  ANNOTATE */;
  ecl_cmp_defun(VV[45]);                          /*  CDFMAT;maxRowIndex;%I;5 */
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[8], ECL_SYM("LOCATION",1862), VVtemp[12], VVtemp[13]) /*  ANNOTATE */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[8], ECL_SYM("LAMBDA-LIST",1000), ECL_NIL, VVtemp[3]) /*  ANNOTATE */;
  ecl_cmp_defun(VV[46]);                          /*  CDFMAT;maxColIndex;%I;6 */
  ecl_function_dispatch(cl_env_copy,VV[40])(3, VV[9], VV[1], VV[10]) /*  PUT */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[9], ECL_SYM("LOCATION",1862), VVtemp[14], VVtemp[15]) /*  ANNOTATE */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[9], ECL_SYM("LAMBDA-LIST",1000), ECL_NIL, VVtemp[16]) /*  ANNOTATE */;
  ecl_cmp_defun(VV[47]);                          /*  CDFMAT;qelt;%2IC;7 */
  ecl_function_dispatch(cl_env_copy,VV[40])(3, VV[11], VV[1], VV[10]) /*  PUT */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[11], ECL_SYM("LOCATION",1862), VVtemp[17], VVtemp[18]) /*  ANNOTATE */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[11], ECL_SYM("LAMBDA-LIST",1000), ECL_NIL, VVtemp[16]) /*  ANNOTATE */;
  ecl_cmp_defun(VV[48]);                          /*  CDFMAT;elt;%2IC;8 */
  ecl_function_dispatch(cl_env_copy,VV[40])(3, VV[12], VV[1], VV[13]) /*  PUT */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[12], ECL_SYM("LOCATION",1862), VVtemp[19], VVtemp[20]) /*  ANNOTATE */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[12], ECL_SYM("LAMBDA-LIST",1000), ECL_NIL, VVtemp[21]) /*  ANNOTATE */;
  ecl_cmp_defun(VV[49]);                          /*  CDFMAT;qsetelt!;%2I2C;9 */
  ecl_function_dispatch(cl_env_copy,VV[40])(3, VV[14], VV[1], VV[13]) /*  PUT */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[14], ECL_SYM("LOCATION",1862), VVtemp[22], VVtemp[23]) /*  ANNOTATE */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[14], ECL_SYM("LAMBDA-LIST",1000), ECL_NIL, VVtemp[21]) /*  ANNOTATE */;
  ecl_cmp_defun(VV[50]);                          /*  CDFMAT;setelt!;%2I2C;10 */
  ecl_function_dispatch(cl_env_copy,VV[40])(3, VV[15], VV[1], VVtemp[24]) /*  PUT */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[15], ECL_SYM("LOCATION",1862), VVtemp[25], VVtemp[26]) /*  ANNOTATE */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[15], ECL_SYM("LAMBDA-LIST",1000), ECL_NIL, VVtemp[27]) /*  ANNOTATE */;
  ecl_cmp_defun(VV[51]);                          /*  CDFMAT;empty;%;11 */
  ecl_function_dispatch(cl_env_copy,VV[40])(3, VV[16], VV[1], VV[17]) /*  PUT */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[16], ECL_SYM("LOCATION",1862), VVtemp[28], VVtemp[29]) /*  ANNOTATE */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[16], ECL_SYM("LAMBDA-LIST",1000), ECL_NIL, VVtemp[30]) /*  ANNOTATE */;
  ecl_cmp_defun(VV[52]);                          /*  CDFMAT;qnew;2Nni%;12 */
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[18], ECL_SYM("LOCATION",1862), VVtemp[31], VVtemp[32]) /*  ANNOTATE */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[18], ECL_SYM("LAMBDA-LIST",1000), ECL_NIL, VVtemp[33]) /*  ANNOTATE */;
  ecl_cmp_defun(VV[53]);                          /*  CDFMAT;new;2NniC%;13 */
  (cl_env_copy->function=(ECL_SYM("MAPC",545)->symbol.gfdef))->cfun.entry(2, ECL_SYM("PROCLAIM",668), VVtemp[34]) /*  MAPC */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[19], ECL_SYM("LOCATION",1862), VVtemp[35], VVtemp[36]) /*  ANNOTATE */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[19], ECL_SYM("LAMBDA-LIST",1000), ECL_NIL, ECL_NIL) /*  ANNOTATE */;
  ecl_cmp_defun(VV[54]);                          /*  ComplexDoubleFloatMatrix; */
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[36], ECL_SYM("LOCATION",1862), VVtemp[37], VVtemp[38]) /*  ANNOTATE */;
  ecl_function_dispatch(cl_env_copy,ECL_SYM("ANNOTATE",1856))(4, VV[36], ECL_SYM("LAMBDA-LIST",1000), ECL_NIL, ECL_NIL) /*  ANNOTATE */;
  ecl_cmp_defun(VV[63]);                          /*  ComplexDoubleFloatMatrix */
 {
  cl_object T0, T1, T2, T3;
  cl_object volatile env0 = ECL_NIL;
  T0 = ecl_function_dispatch(cl_env_copy,VV[65])(2, ecl_make_fixnum(11), VVtemp[41]) /*  makeByteWordVec2 */;
  T1 = ecl_function_dispatch(cl_env_copy,VV[65])(2, ecl_make_fixnum(48), VVtemp[44]) /*  makeByteWordVec2 */;
  T2 = cl_listX(4, T0, VVtemp[42], VVtemp[43], T1);
  T3 = cl_list(5, VVtemp[39], VVtemp[40], ECL_NIL, T2, VV[39]);
  ecl_function_dispatch(cl_env_copy,VV[66])(3, VV[36], VV[38], T3) /*  MAKEPROP */;
 }
}
