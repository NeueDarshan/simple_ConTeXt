% SYNTAX TEST "Packages/simple_ConTeXt/MetaPost.sublime-syntax"

% <- source.metapost

  prologues := 3;
% ^^^^^^^^^       variable.language.metapost
%           ^^    keyword.operator.metapost
%              ^  constant.numeric.metapost
%               ^ punctuation.terminator.semicolon.metapost
  outputtemplate := "%j-%c.mps";
% ^^^^^^^^^^^^^^                 variable.language.metapost
%                ^^              keyword.operator.metapost
%                   ^            punctuation.definition.string.begin.metapost
%                    ^^          constant.other.placeholder.metapost
%                       ^^       constant.other.placeholder.metapost
%                             ^  punctuation.definition.string.end.metapost
%                   ^^^^^^^^^^^  string.quoted.double.metapost
%                              ^ punctuation.terminator.semicolon.metapost

  % numbersystem := "decimal";
% ^                            punctuation.definition.comment.metapost
% ^^^^^^^^^^^^^^^^^^^^^^^^^^^^ comment.line.percentage.metapost

  beginfig(1);
% ^^^^^^^^     support.function.metapost
%         ^    punctuation.section.parens.begin.metapost
%          ^   entity.name.section.metapost constant.numeric.metapost
%           ^  punctuation.section.parens.end.metapost
%         ^^^  meta.parens.metapost
%            ^ punctuation.terminator.semicolon.metapost

    boolean a; color b; rgbcolor c; cmykcolor d; numeric e; pair f;
  % ^^^^^^^                                                         storage.type.metapost
  %          ^                                                      punctuation.terminator.semicolon.metapost
  %            ^^^^^                                                storage.type.metapost
  %                   ^                                             punctuation.terminator.semicolon.metapost
  %                     ^^^^^^^^                                    storage.type.metapost
  %                               ^                                 punctuation.terminator.semicolon.metapost
  %                                 ^^^^^^^^^                       storage.type.metapost
  %                                            ^                    punctuation.terminator.semicolon.metapost
  %                                              ^^^^^^^            storage.type.metapost
  %                                                       ^         punctuation.terminator.semicolon.metapost
  %                                                         ^^^^    storage.type.metapost
  %                                                               ^ punctuation.terminator.semicolon.metapost

    path g; pen h; picture i; string j; transform k;
  % ^^^^                                             storage.type.metapost
  %       ^                                          punctuation.terminator.semicolon.metapost
  %         ^^^                                      storage.type.metapost
  %              ^                                   punctuation.terminator.semicolon.metapost
  %                ^^^^^^^                           storage.type.metapost
  %                         ^                        punctuation.terminator.semicolon.metapost
  %                           ^^^^^^                 storage.type.metapost
  %                                   ^              punctuation.terminator.semicolon.metapost
  %                                     ^^^^^^^^^    storage.type.metapost
  %                                                ^ punctuation.terminator.semicolon.metapost

    a := not (true or false);
  %   ^^                      keyword.operator.metapost
  %      ^^^                  keyword.operator.word.metapost
  %           ^^^^            constant.language.metapost
  %                ^^         keyword.operator.word.metapost
  %                   ^^^^^   constant.language.metapost
  %                         ^ punctuation.terminator.semicolon.metapost

  b := 0.5[blue, red];
  % ^^                 keyword.operator.metapost
  %    ^^^             constant.numeric.metapost
  %        ^^^^        constant.language.metapost
  %              ^^^   constant.language.metapost
  %                  ^ punctuation.terminator.semicolon.metapost

  e := 1bp + 2cc + 3cm + 4dd + 5in + 6mm + 7pc + 8pt;
  % ^^                                                keyword.operator.metapost
  %    ^                                              constant.numeric.metapost
  %     ^^                                            keyword.other.unit.metapost
  %        ^                                          keyword.operator.metapost
  %          ^                                        constant.numeric.metapost
  %           ^^                                      keyword.other.unit.metapost
  %              ^                                    keyword.operator.metapost
  %                ^                                  constant.numeric.metapost
  %                 ^^                                keyword.other.unit.metapost
  %                    ^                              keyword.operator.metapost
  %                      ^                            constant.numeric.metapost
  %                       ^^                          keyword.other.unit.metapost
  %                          ^                        keyword.operator.metapost
  %                            ^                      constant.numeric.metapost
  %                             ^^                    keyword.other.unit.metapost
  %                                ^                  keyword.operator.metapost
  %                                  ^                constant.numeric.metapost
  %                                   ^^              keyword.other.unit.metapost
  %                                      ^            keyword.operator.metapost
  %                                        ^          constant.numeric.metapost
  %                                         ^^        keyword.other.unit.metapost
  %                                            ^      keyword.operator.metapost
  %                                              ^    constant.numeric.metapost
  %                                               ^^  keyword.other.unit.metapost
  %                                                 ^ punctuation.terminator.semicolon.metapost

    j := "string";
  %   ^^           keyword.operator.metapost
  %      ^         punctuation.definition.string.begin.metapost
  %             ^  punctuation.definition.string.end.metapost
  %      ^^^^^^^^  string.quoted.double.metapost
  %              ^ punctuation.terminator.semicolon.metapost

  g := origin .. (1,1) -- (2,2) ... (3,3) {dir 30}..{up} (4,4) ..{curl 5} (5,5) ..tension 1.5 and 1.. (6,6) ..controls (1,-1) and (1,1).. cycle;
  % ^^                                                                                                                                           keyword.operator.metapost
  %    ^^^^^^                                                                                                                                    constant.language.metapost
  %           ^^                                                                                                                                 keyword.operator.metapost
  %               ^                                                                                                                              constant.numeric.metapost
  %                 ^                                                                                                                            constant.numeric.metapost
  %                    ^^                                                                                                                        keyword.operator.metapost
  %                        ^                                                                                                                     constant.numeric.metapost
  %                          ^                                                                                                                   constant.numeric.metapost
  %                             ^^^                                                                                                              keyword.operator.metapost
  %                                  ^                                                                                                           constant.numeric.metapost
  %                                    ^                                                                                                         constant.numeric.metapost
  %                                        ^^^                                                                                                   support.function.metapost
  %                                            ^^                                                                                                constant.numeric.metapost
  %                                               ^^                                                                                             keyword.operator.metapost
  %                                                  ^^                                                                                          constant.language.metapost
  %                                                       ^                                                                                      constant.numeric.metapost
  %                                                         ^                                                                                    constant.numeric.metapost
  %                                                            ^^                                                                                keyword.operator.metapost
  %                                                               ^^^^                                                                           keyword.operator.word.metapost
  %                                                                    ^                                                                         constant.numeric.metapost
  %                                                                        ^                                                                     constant.numeric.metapost
  %                                                                          ^                                                                   constant.numeric.metapost
  %                                                                             ^^                                                               keyword.operator.metapost
  %                                                                               ^^^^^^^                                                        keyword.operator.word.metapost
  %                                                                                       ^^^                                                    constant.numeric.metapost
  %                                                                                           ^^^                                                keyword.operator.word.metapost
  %                                                                                               ^                                              constant.numeric.metapost
  %                                                                                                ^^                                            keyword.operator.metapost
  %                                                                                                    ^                                         constant.numeric.metapost
  %                                                                                                      ^                                       constant.numeric.metapost
  %                                                                                                         ^^                                   keyword.operator.metapost
  %                                                                                                           ^^^^^^^                            keyword.operator.word.metapost
  %                                                                                                                     ^                        constant.numeric.metapost
  %                                                                                                                        ^                     constant.numeric.metapost
  %                                                                                                                           ^^^                keyword.operator.word.metapost
  %                                                                                                                                ^             constant.numeric.metapost
  %                                                                                                                                  ^           constant.numeric.metapost
  %                                                                                                                                    ^^        keyword.operator.metapost
  %                                                                                                                                       ^^^^^  support.function.metapost
  %                                                                                                                                            ^ punctuation.terminator.semicolon.metapost

    % draw g scaled 1cm dashed evenly withcolor red;
    % labeloffset := 0.5cm;
    % pair p; p := origin shifted (1pt, 1bp);
    % dotlabel("p", p);

    begingroup;
  % ^^^^^^^^^^  support.function.metapost
  %           ^ punctuation.terminator.semicolon.metapost
      interim labeloffset := 1cm;
    % ^^^^^^^                     storage.modifier.metapost
    %         ^^^^^^^^^^^         variable.language.metapost
    %                     ^^      keyword.operator.metapost
    %                        ^    constant.numeric.metapost
    %                         ^^  keyword.other.unit.metapost
    %                           ^ punctuation.terminator.semicolon.metapost

      save p; pair p; p := origin;
    % ^^^^                         storage.modifier.metapost
    %       ^                      punctuation.terminator.semicolon.metapost
    %         ^^^^                 storage.type.metapost
    %               ^              punctuation.terminator.semicolon.metapost
    %                   ^^         keyword.operator.metapost
    %                      ^^^^^^  constant.language.metapost
    %                            ^ punctuation.terminator.semicolon.metapost

      picture pic;
      pic := thelabel.top(
        btex
      % ^^^^ support.function.metapost
          $\displaystyle \sum_{n=1}^{\infty} n = -\frac{1}{12}$
      % <- text.tex.embedded.metapost
        etex,
      % ^^^^ support.function.metapost
        p
      );

      unfill bbox pic;
      draw pic withcolor blue;
    endgroup;
  % ^^^^^^^^  support.function.metapost
  %         ^ punctuation.terminator.semicolon.metapost

    def circle expr theta = (cosd(theta), sind(theta)) enddef
  % ^^^                                                       storage.type.metapost
  %     ^^^^^^                                                entity.name.function.metapost
  %            ^^^^                                           storage.modifier.metapost
  %                 ^^^^^                                     variable.parameter.metapost
  %                       ^                                   keyword.operator.assignment.metapost
  %                                                    ^^^^^^ storage.type.metapost

    path q;
    q := origin for i=0,90,10: .. circle(i) endfor;
  %             ^^^                                keyword.control.conditional.metapost
  %                                         ^^^^^^ keyword.control.conditional.metapost

  endfig;
% ^^^^^^  support.function.metapost
%       ^ punctuation.terminator.semicolon.metapost

  end
% ^^^ support.function.metapost
