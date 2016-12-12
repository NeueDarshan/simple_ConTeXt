% SYNTAX TEST "Packages/ConTeXtTools/MetaPost.sublime-syntax"

% <- source.metapost

prologues := 3;
outputtemplate := "%j-%c.mps";
% <-                         variable.parameter.internal.metapost
%              ^^            keyword.operator.metapost
%                  ^^        constant.other.escape.metapost
%                     ^^     constant.other.escape.metapost
%                       ^^^^ string.metapost
outputformat := "svg";
% numbersystem := "decimal";
% <- comment.metapost

beginfig(1);
% <- support.class.metapost
    boolean a;
      color b;
   rgbcolor c;
  cmykcolor d;
    numeric e;
       pair f;
       path g;
        pen h;
    picture i;
     string j;
  transform k;
  % <- storage.type.metapost

  a := not (true or false);
  b := 0.5[blue, red];
  e := 1bp + 2cc + 3cm + 4dd + 5in + 6mm + 7pc + 8pt;
  j := "string";

  g := origin ..
       (1,1)  --
       (2,2)  ...
       (3,3)  {dir 30}..{up}
       (4,4)  ..{curl 5}
       (5,5)  ..tension 1.5 and 1..
       (6,6)  ..controls (1,-1) and (1,1)..
       cycle;
  draw g scaled 1cm dashed evenly withcolor red;

  labeloffset := 0.5cm;
  pair p; p := origin shifted (1pt, 1bp);
  dotlabel("p", p);

  begingroup;
  % <- support.class.metapost
    interim labeloffset := 1cm;
    save p; pair p; p := origin;

    picture pic;
    pic := thelabel.top(
      btex
      % <- text.tex
        $\displaystyle \sum_{n=1}^{\infty} \frac{1}{n} = -\frac{1}{12}$
      etex,
      p
    );

    unfill bbox pic;
    draw pic withcolor blue;
  endgroup;
  % <- support.class.metapost

  def circle(expr theta) = (cosd(theta), sind(theta)) enddef
  % <-                                                       support.class.metapost
  %   ^^^^^^                                                 entity.name.function.metapost
  %          ^^^^                                            storage.type.metapost
  %               ^^^^^                                      variable.parameter.metapost
  %                      ^                                   keyword.operator.metapost
  %                                                   ^^^^^^ support.class.metapost
  path q;
  q := origin for i=0,90,10: .. circle(i) endfor;
  %           ^^^                                keyword.metapost
  %                                       ^^^^^^ keyword.metapost
endfig;
% <- support.class.metapost

end
% <- support.class.metapost
