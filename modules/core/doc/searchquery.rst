Building Search Queries
=======================

You can filter most results by building complex search queries.

Search query form (EBNF)::

   letter   = ? characters from "a" to "z" ?
   keychar  = letter | "_" | "-"
   valchar  = ? printable characters exept "," and ";" ?
   and      = ","
   or       = ";"

   operator = letter , { letter } ;
   key      = keychars, { keychars } ;
   value    = { valchars } ;

   search   = operator, ":", key, ":", value
   query    = search
            | search, and, search
            | search, or, search ;

Search example::

   http://...?q=eq:identifier:example
     -> Return objects which identifier equals “example”

   http://...?q=eq:identifier:example,gt:version:5
     -> Return objects which identifier equals “example” and which version
        number is greater than 5

**Types and operators**:

Type: *uuid*

   The value will fist be converted to a UUIDv4. The value can have either
   the form of a uuid or a hexadecimal string. Invalid values will raise an
   error.

   ===  =========
   eq   Equal
   neq  Not equal
   ===  =========

Type: *int*

   The value will first be converted to an integer. Invalid values will
   raise an error.

   ===  ================
   eq   Equal
   neq  Not equal
   lt   Lower than
   gt   Greater than
   leq  Lower or equal
   geq  Greater or equal
   ===  ================

Type: *str*

   The string value will be escaped to prevent SQL injection attacks. To
   enable the use of special characters the string can be base64 encoded. In
   that case the string must have the prefix "base64:"

   Base64 example::

      <op>:<key>:one, two
        -> Will not work because of the ",". Use:
      <op>:<key>:base64:b25lLCB0d28=

   ==========  =======================================
   eq          Equal
   neq         Not equal
   in          Search value is substring
   startswith  Database value starts with search value
   endswith    Database value ends with search value
   ==========  =======================================

Type: *time*

   The value must be either in the ISO datetime format (YYYY-MM-DD HH:MM:SS)
   or in RFC2822 datetime format. Invalid values will raise an error.

   ===  ================
   eq   Equal
   neq  Not equal
   lt   Lower than
   gt   Greater than
   leq  Lower or equal
   geq  Greater or equal
   ===  ================

Type: *lang*

   Check if the value is a IETF Language Tag. Only the form will be checked,
   not if the language tag is a proper registered tag. Invalid values will
   raise an error.

   ==========  =====================================
   eq          Equal
   neq         Not equal
   in          Search value is substring
   startswith  Language tag starts with search value
   ==========  =====================================
