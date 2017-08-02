% SYNTAX TEST "Packages/simple_ConTeXt/MetaPost.sublime-syntax"

% <- source.metapost

  prologues := 3;
% ^^^^^^^^^       constant.language.metapost
%           ^^    keyword.operator.metapost
%              ^  constant.numeric.metapost
%               ^ punctuation.terminator.semicolon.metapost
  outputtemplate := "%j-%c.mps";
% ^^^^^^^^^^^^^^                 constant.language.metapost
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
% ^^^^^^^^     entity.name.other.fig.metapost
%         ^    punctuation.section.parens.begin.metapost
%          ^   constant.numeric.metapost meta.other.numeric.fig.metapost
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
  %          ^                punctuation.section.parens.begin.metapost
  %           ^^^^            constant.language.metapost
  %                ^^         keyword.operator.word.metapost
  %                   ^^^^^   constant.language.metapost
  %                        ^  punctuation.section.parens.end.metapost
  %          ^^^^^^^^^^^^^^^  meta.parens.metapost
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
  %                                        ^^^                                                                                                   support.function.general.metapost
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
  %                                                                                                                                       ^^^^^  support.function.general.metapost
  %                                                                                                                                            ^ punctuation.terminator.semicolon.metapost

    % draw g scaled 1cm dashed evenly withcolor red;
    % labeloffset := 0.5cm;
    % pair p; p := origin shifted (1pt, 1bp);
    % dotlabel("p", p);

    begingroup;
  % ^^^^^^^^^^  entity.name.other.group.metapost
  %           ^ punctuation.terminator.semicolon.metapost
      interim labeloffset := 1cm;
    % ^^^^^^^                     storage.modifier.metapost
    %         ^^^^^^^^^^^         constant.language.metapost
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
      % ^^^^ entity.name.other.tex.metapost
          $\displaystyle \sum_{n=1}^{\infty} n = -\frac{1}{12}$
      % <- text.tex.embedded.metapost
        etex,
      % ^^^^ entity.name.other.tex.metapost
        p
      );

      unfill bbox pic;
      draw pic withcolor blue;
    endgroup;
  % ^^^^^^^^  entity.name.other.group.metapost
  %         ^ punctuation.terminator.semicolon.metapost

    def circle expr theta = (cosd(theta), sind(theta)) enddef
  % ^^^                                                       storage.type.function.general.metapost
  %     ^^^^^^                                                entity.name.function.metapost meta.other.function.def.metapost
  %            ^^^^                                           storage.type.metapost
  %                 ^^^^^                                     variable.parameter.metapost
  %                       ^                                   keyword.operator.metapost
  %                                                    ^^^^^^ storage.type.function.general.metapost

    path q;
    q := origin for i=0,90,10: .. circle(i) endfor;
  %             ^^^                                keyword.control.metapost
  %                                         ^^^^^^ keyword.control.metapost

  endfig;
% ^^^^^^  entity.name.other.fig.metapost
%       ^ punctuation.terminator.semicolon.metapost

  end
% ^^^ entity.name.other.end.metapost
