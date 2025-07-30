import 'dart:io';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flet/flet.dart';
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

class FletSvgControl extends StatelessWidget {
  final Control? parent;
  final Control control;

  const FletSvgControl({
    super.key,
    required this.parent,
    required this.control,
  });

  @override
  Widget build(BuildContext context) {
    String src = control.attrString('src') ?? '';
    String kind = control.attrString('kind') ?? 'network';
    String? key = control.attrString('key');
    String fitStr = control.attrString('fit') ?? 'contain';
    String alignmentStr = control.attrString('alignment') ?? 'center';
    double? width = control.attrDouble('width');
    double? height = control.attrDouble('height');
    bool matchTextDirection = control.attrBool('match_text_direction') ?? false;
    bool allowDrawingOutsideViewBox = control.attrBool('allow_drawing_outside_view_box') ?? false;
    String? semanticsLabel = control.attrString('semantics_label');
    bool excludeFromSemantics = control.attrBool('exclude_from_semantics') ?? false;
    String clipBehaviorStr = control.attrString('clip_behavior') ?? 'hard_edge';
    BoxFit fit = switch(fitStr) {
      'fill' => BoxFit.fill,
      'cover' => BoxFit.cover,
      'fit_width' => BoxFit.fitWidth,
      'fit_height' => BoxFit.fitHeight,
      'none' => BoxFit.none,
      'scale_down' => BoxFit.scaleDown,
      _ => BoxFit.contain,
    };
    AlignmentGeometry alignment = switch(alignmentStr) {
      'bottom_right' => Alignment.bottomRight,
      'bottom_center' => Alignment.bottomCenter,
      'bottom_left' => Alignment.bottomLeft,
      'top_right' => Alignment.topRight,
      'top_center' => Alignment.topCenter,
      'top_left' => Alignment.topLeft,
      _ => Alignment.center,
    };
    Clip clipBehavior = switch(clipBehaviorStr) {
      'none' => Clip.none,
      'anti_alias' => Clip.antiAlias,
      'anti_alias_with_save_layer' => Clip.antiAliasWithSaveLayer,
      _ => Clip.hardEdge,
    };

    Widget myControl = switch(kind) {
      'asset' => SvgPicture.asset(
        src,
        key: key != null ? Key(key) : null,
        width: width,
        height: height,
        fit: fit,
        alignment: alignment,
        matchTextDirection: matchTextDirection,
        allowDrawingOutsideViewBox: allowDrawingOutsideViewBox,
        semanticsLabel: semanticsLabel,
        excludeFromSemantics: excludeFromSemantics,
        clipBehavior: clipBehavior
      ),
      'file' => SvgPicture.file(
        File(src),
        key: key != null ? Key(key) : null,
        width: width,
        height: height,
        fit: fit,
        alignment: alignment,
        matchTextDirection: matchTextDirection,
        allowDrawingOutsideViewBox: allowDrawingOutsideViewBox,
        semanticsLabel: semanticsLabel,
        excludeFromSemantics: excludeFromSemantics,
        clipBehavior: clipBehavior
      ),
      'network' => SvgPicture.network(
        src,
        key: key != null ? Key(key) : null,
        width: width,
        height: height,
        fit: fit,
        alignment: alignment,
        matchTextDirection: matchTextDirection,
        allowDrawingOutsideViewBox: allowDrawingOutsideViewBox,
        semanticsLabel: semanticsLabel,
        excludeFromSemantics: excludeFromSemantics,
        clipBehavior: clipBehavior
      ),
      'memory' => SvgPicture.memory(
        Uint8List.fromList(utf8.encode(src)),
        key: key != null ? Key(key) : null,
        width: width,
        height: height,
        fit: fit,
        alignment: alignment,
        matchTextDirection: matchTextDirection,
        allowDrawingOutsideViewBox: allowDrawingOutsideViewBox,
        semanticsLabel: semanticsLabel,
        excludeFromSemantics: excludeFromSemantics,
        clipBehavior: clipBehavior
      ),
      _ => SvgPicture.string(
        src,
        key: key != null ? Key(key) : null,
        width: width,
        height: height,
        fit: fit,
        alignment: alignment,
        matchTextDirection: matchTextDirection,
        allowDrawingOutsideViewBox: allowDrawingOutsideViewBox,
        semanticsLabel: semanticsLabel,
        excludeFromSemantics: excludeFromSemantics,
        clipBehavior: clipBehavior
      ),
    };

    return constrainedControl(context, myControl, parent, control);
  }
}
