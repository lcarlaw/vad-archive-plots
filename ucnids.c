/********************************************************************
* ucnids - NIDS decompression utility for data compressed with zlib
*
*   syntax: ucnids [options] ifile ofile
*   ifile and ofile can be "-" to use standard input and output
*   options: 
*     none - output uncompressed product with NOAAPORT CCB
*     -c   - output with standard WMO CCB
*     -r   - output with strippped WMO CCB (RPS output)
*     -w   - output with WXP-like WMO header
*     -n   - output stripping header and leaving raw NIDS data
********************************************************************/
#include <stdio.h>
#include <zlib.h>

mkdirs( char *path ){
   int len;
   int i;

   len = strlen( path );

   for( i = 1; i < len-1; i++ ){
      if( path[i] == '/' ){
         path[i] = 0;
         mkdir( path, 0755 );
         path[i] = '/';
         }
      }
   }

main( int argc, char **argv ){
   FILE *ifile;
   FILE *ofile;
   unsigned char soh[101];
   unsigned char seq[101];
   unsigned char wmo[101];
   unsigned char awip[101];
   unsigned char inbuf[1000];
   unsigned int insize;
   unsigned char outbuf[10000];
   z_stream zs;
   int out;
   int len;
   int iret;
   int off;
   int i;
   int verb;
   int wxp;
   int inbytes;
   int outbytes;
   int check;
   inbytes=0; //MK
   verb = 0;

   off = 0;
   if( argc > 1 && !strcmp( argv[1], "-c" )){
      out = 1;
      off++;
      }
   if( argc > 1 && !strcmp( argv[1], "-w" )){
      out = 2;
      off++;
      }
   if( argc > 1 && !strcmp( argv[1], "-n" )){
      out = 3;
      off++;
      }
   if( argc > 1 && !strcmp( argv[1], "-r" )){
      out = 4;
      off++;
      }
   if( argc == 1+off || argv[1+off][0] == '-' )
      ifile = stdin;
   else
      ifile = fopen( argv[1+off], "rb" );
   if( ifile == NULL ) exit( 1 );

   if( argc < 3+off || argv[2+off][0] == '-' )
      ofile = stdin;
   else {
      mkdirs( argv[2+off] );
      ofile = fopen( argv[2+off], "wb" );
      if( !ofile ) exit( 1 );
      }
  
   fgets( soh, 100, ifile );
   /*
      Account for both raw input (0x01) and WXP input (**)
   */
   wxp = 0;
   off = 0;
   check = ((soh[0] << 8 + soh[1]) % 31);
   if( check == 0 ){
      off = strlen( soh );
      memcpy( inbuf, soh, off );
      }
   else if( soh[0] == '\n' ){
      fgets( soh, 100, ifile );
      len = strlen( soh )-7;
      memcpy( wmo, soh+3, len );
      wmo[len] = 0;
      fgets( awip, 100, ifile );
      wxp = 1;
      }
   else if( soh[0] == '*' ){
      len = strlen( soh )-7;
      memcpy( wmo, soh+3, len );
      wmo[len] = 0;
      fgets( awip, 100, ifile );
      wxp = 1;
      }
   else if( soh[0] == 0x01 ){
      fgets( seq, 100, ifile );
      fgets( wmo, 100, ifile );
      fgets( awip, 100, ifile );
      }

   iret = 0;
   zs.total_out = 4000;
   
   for( i = 0; iret != Z_STREAM_END || zs.total_out == 4000; i++ ){
      /* 
         Read in a block of data
      */
      insize = fread( inbuf+off, 1, 1000-off, ifile ); 
      //fprintf( stderr, "Read: %d %d %d\n", off, insize, iret );
      if( off == 0 && insize == 0 ) break;
      inbytes+=insize;
      len = insize + off;
      /* 
         Check for 789C byte sequence denoting zlib compression
         If data are not compressed, pass through raw data
      */
      check = (((inbuf[0] << 8) + inbuf[1]) % 31);
      if( i == 0 && check != 0 ){
          if( wxp ){
             if( out == 1 ){
                fwrite( "\001\r\r\n001\r\r\n", 1, 10, ofile );
                fprintf( ofile, "%18.18s\r\r\n", wmo );
                }
             else if( out == 2 ){
                fprintf( ofile, soh );
                fprintf( ofile, awip );
                }
             }
          else {
             if( out == 1 ){
                fprintf( ofile, soh );
                fprintf( ofile, seq );
                fprintf( ofile, wmo );
                fprintf( ofile, awip );
                }
             else if( out == 2 ){
                fprintf( ofile, "** %18.18s ***\n%s", wmo, awip );
                }
             }
          fwrite( inbuf, 1, insize, ofile );
          while(( insize = fread( inbuf, 1, 1000, ifile )) > 0 ){
             fwrite( inbuf, 1, insize, ofile );
             }
          exit( 0 );
          }
      if( check == 0 || iret != Z_STREAM_END ){
         zs.avail_in = len;
         zs.avail_out = 10000;
         zs.next_in = inbuf;
         zs.next_out = outbuf;
         /*
            Check to see if 4000 byte block has been read and reinitialize
         */
         if( i == 0 || iret == Z_STREAM_END ){
            zs.zalloc = NULL;
            zs.zfree = NULL;
            inflateInit( &zs );
            }
         /*
            Inflate NIDS data
         */
         iret = inflate( &zs, Z_STREAM_END );
         if( verb ) fprintf( stderr, "Inf: %d -- %d %d %d -- 10000 %d %d -- %2X %2X\n", 
            iret, len, zs.avail_in, zs.total_in, zs.avail_out, zs.total_out, 
            inbuf[0], inbuf[1] );
         off = zs.avail_in;
         }
      else {
         memcpy( outbuf, inbuf, len );
         zs.avail_out = 10000-len;
         off = 0;
         if( verb ) fprintf( stderr, "Cpy: %d\n", len );
         }
      /*  
         Process header data for first block
         WMO CCB output
      */
      if( i == 0 && out == 1 ){
         fwrite( "\001\r\r\n001\r\r\n", 1, 10, ofile );
         fwrite( outbuf+24, 1, 10000-zs.avail_out-24, ofile );
         } 
      /*
         WXP header output
      */
      else if( i == 0 && out == 2 ){
         fprintf( ofile, "** %18.18s ***\n%s", wmo, awip );
         fwrite( outbuf+54, 1, 10000-zs.avail_out-54, ofile );
         } 
      /*
         Raw NIDS output
      */
      else if( i == 0 && out == 3 ){
         fwrite( outbuf+54, 1, 10000-zs.avail_out-54, ofile );
         outbytes+=10000-zs.avail_out-54;
         } 
      /*
         Stripped WMO CCB output
      */
      else if( i == 0 && out == 4 ){
         fwrite( outbuf+24, 1, 10000-zs.avail_out-24, ofile );
         } 
      /*
         Raw output with NOAAPORT CCB
      */
      else {
         fwrite( outbuf, 1, 10000-zs.avail_out, ofile );
         outbytes+=10000-zs.avail_out;
         } 
      /*
         Move remaining data that still is compressed and prepared 
         for next inflate
      */
      memcpy( inbuf, inbuf+len-off, off );
      if( iret < 0 ) break;
      }
   exit( 0 );
   }