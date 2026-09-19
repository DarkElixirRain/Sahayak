// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint, type=warning, deprecated_member_use, deprecated_member_use_from_same_package
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'chat_models.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$ConversationMessage {

 String get role; String get content;@JsonKey(name: 'created_at') String? get createdAt; String? get audio; List<Citation> get citations; bool get grounded; String? get status; String? get disclaimer;
/// Create a copy of ConversationMessage
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ConversationMessageCopyWith<ConversationMessage> get copyWith => _$ConversationMessageCopyWithImpl<ConversationMessage>(this as ConversationMessage, _$identity);

  /// Serializes this ConversationMessage to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ConversationMessage&&(identical(other.role, role) || other.role == role)&&(identical(other.content, content) || other.content == content)&&(identical(other.createdAt, createdAt) || other.createdAt == createdAt)&&(identical(other.audio, audio) || other.audio == audio)&&const DeepCollectionEquality().equals(other.citations, citations)&&(identical(other.grounded, grounded) || other.grounded == grounded)&&(identical(other.status, status) || other.status == status)&&(identical(other.disclaimer, disclaimer) || other.disclaimer == disclaimer));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,role,content,createdAt,audio,const DeepCollectionEquality().hash(citations),grounded,status,disclaimer);

@override
String toString() {
  return 'ConversationMessage(role: $role, content: $content, createdAt: $createdAt, audio: $audio, citations: $citations, grounded: $grounded, status: $status, disclaimer: $disclaimer)';
}


}

/// @nodoc
abstract mixin class $ConversationMessageCopyWith<$Res>  {
  factory $ConversationMessageCopyWith(ConversationMessage value, $Res Function(ConversationMessage) _then) = _$ConversationMessageCopyWithImpl;
@useResult
$Res call({
 String role, String content,@JsonKey(name: 'created_at') String? createdAt, String? audio, List<Citation> citations, bool grounded, String? status, String? disclaimer
});




}
/// @nodoc
class _$ConversationMessageCopyWithImpl<$Res>
    implements $ConversationMessageCopyWith<$Res> {
  _$ConversationMessageCopyWithImpl(this._self, this._then);

  final ConversationMessage _self;
  final $Res Function(ConversationMessage) _then;

/// Create a copy of ConversationMessage
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? role = null,Object? content = null,Object? createdAt = freezed,Object? audio = freezed,Object? citations = null,Object? grounded = null,Object? status = freezed,Object? disclaimer = freezed,}) {
  return _then(ConversationMessage(
role: null == role ? _self.role : role // ignore: cast_nullable_to_non_nullable
as String,content: null == content ? _self.content : content // ignore: cast_nullable_to_non_nullable
as String,createdAt: freezed == createdAt ? _self.createdAt : createdAt // ignore: cast_nullable_to_non_nullable
as String?,audio: freezed == audio ? _self.audio : audio // ignore: cast_nullable_to_non_nullable
as String?,citations: null == citations ? _self.citations : citations // ignore: cast_nullable_to_non_nullable
as List<Citation>,grounded: null == grounded ? _self.grounded : grounded // ignore: cast_nullable_to_non_nullable
as bool,status: freezed == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String?,disclaimer: freezed == disclaimer ? _self.disclaimer : disclaimer // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [ConversationMessage].
extension ConversationMessagePatterns on ConversationMessage {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _ConversationMessage value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ConversationMessage() when $default != null:
return $default(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _ConversationMessage value)  $default,){
final _that = this;
switch (_that) {
case _ConversationMessage():
return $default(_that);}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _ConversationMessage value)?  $default,){
final _that = this;
switch (_that) {
case _ConversationMessage() when $default != null:
return $default(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( String role,  String content, @JsonKey(name: 'created_at')  String? createdAt,  String? audio,  List<Citation> citations,  bool grounded,  String? status,  String? disclaimer)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ConversationMessage() when $default != null:
return $default(_that.role,_that.content,_that.createdAt,_that.audio,_that.citations,_that.grounded,_that.status,_that.disclaimer);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( String role,  String content, @JsonKey(name: 'created_at')  String? createdAt,  String? audio,  List<Citation> citations,  bool grounded,  String? status,  String? disclaimer)  $default,) {final _that = this;
switch (_that) {
case _ConversationMessage():
return $default(_that.role,_that.content,_that.createdAt,_that.audio,_that.citations,_that.grounded,_that.status,_that.disclaimer);}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( String role,  String content, @JsonKey(name: 'created_at')  String? createdAt,  String? audio,  List<Citation> citations,  bool grounded,  String? status,  String? disclaimer)?  $default,) {final _that = this;
switch (_that) {
case _ConversationMessage() when $default != null:
return $default(_that.role,_that.content,_that.createdAt,_that.audio,_that.citations,_that.grounded,_that.status,_that.disclaimer);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _ConversationMessage implements ConversationMessage {
  const _ConversationMessage({required this.role, this.content = '', @JsonKey(name: 'created_at') this.createdAt, this.audio,  List<Citation> citations = const <Citation>[], this.grounded = false, this.status, this.disclaimer}): _citations = citations;
  factory _ConversationMessage.fromJson(Map<String, dynamic> json) => _$ConversationMessageFromJson(json);

@override final  String role;
@override@JsonKey() final  String content;
@override@JsonKey(name: 'created_at') final  String? createdAt;
@override final  String? audio;
 final  List<Citation> _citations;
@override@JsonKey() List<Citation> get citations {
  if (_citations is EqualUnmodifiableListView) return _citations;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_citations);
}

@override@JsonKey() final  bool grounded;
@override final  String? status;
@override final  String? disclaimer;

/// Create a copy of ConversationMessage
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ConversationMessageCopyWith<_ConversationMessage> get copyWith => __$ConversationMessageCopyWithImpl<_ConversationMessage>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ConversationMessageToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ConversationMessage&&(identical(other.role, role) || other.role == role)&&(identical(other.content, content) || other.content == content)&&(identical(other.createdAt, createdAt) || other.createdAt == createdAt)&&(identical(other.audio, audio) || other.audio == audio)&&const DeepCollectionEquality().equals(other._citations, _citations)&&(identical(other.grounded, grounded) || other.grounded == grounded)&&(identical(other.status, status) || other.status == status)&&(identical(other.disclaimer, disclaimer) || other.disclaimer == disclaimer));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,role,content,createdAt,audio,const DeepCollectionEquality().hash(_citations),grounded,status,disclaimer);

@override
String toString() {
  return 'ConversationMessage(role: $role, content: $content, createdAt: $createdAt, audio: $audio, citations: $citations, grounded: $grounded, status: $status, disclaimer: $disclaimer)';
}


}

/// @nodoc
abstract mixin class _$ConversationMessageCopyWith<$Res> implements $ConversationMessageCopyWith<$Res> {
  factory _$ConversationMessageCopyWith(_ConversationMessage value, $Res Function(_ConversationMessage) _then) = __$ConversationMessageCopyWithImpl;
@override @useResult
$Res call({
 String role, String content,@JsonKey(name: 'created_at') String? createdAt, String? audio, List<Citation> citations, bool grounded, String? status, String? disclaimer
});




}
/// @nodoc
class __$ConversationMessageCopyWithImpl<$Res>
    implements _$ConversationMessageCopyWith<$Res> {
  __$ConversationMessageCopyWithImpl(this._self, this._then);

  final _ConversationMessage _self;
  final $Res Function(_ConversationMessage) _then;

/// Create a copy of ConversationMessage
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? role = null,Object? content = null,Object? createdAt = freezed,Object? audio = freezed,Object? citations = null,Object? grounded = null,Object? status = freezed,Object? disclaimer = freezed,}) {
  return _then(_ConversationMessage(
role: null == role ? _self.role : role // ignore: cast_nullable_to_non_nullable
as String,content: null == content ? _self.content : content // ignore: cast_nullable_to_non_nullable
as String,createdAt: freezed == createdAt ? _self.createdAt : createdAt // ignore: cast_nullable_to_non_nullable
as String?,audio: freezed == audio ? _self.audio : audio // ignore: cast_nullable_to_non_nullable
as String?,citations: null == citations ? _self._citations : citations // ignore: cast_nullable_to_non_nullable
as List<Citation>,grounded: null == grounded ? _self.grounded : grounded // ignore: cast_nullable_to_non_nullable
as bool,status: freezed == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String?,disclaimer: freezed == disclaimer ? _self.disclaimer : disclaimer // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$Citation {

 String get document; String get section; String get provision; String get source; double get score;@JsonKey(name: 'source_url') String? get sourceUrl;@JsonKey(name: 'section_title') String? get sectionTitle;@JsonKey(name: 'is_verified') bool get isVerified;@JsonKey(name: 'currentness_status') String get currentnessStatus;
/// Create a copy of Citation
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$CitationCopyWith<Citation> get copyWith => _$CitationCopyWithImpl<Citation>(this as Citation, _$identity);

  /// Serializes this Citation to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is Citation&&(identical(other.document, document) || other.document == document)&&(identical(other.section, section) || other.section == section)&&(identical(other.provision, provision) || other.provision == provision)&&(identical(other.source, source) || other.source == source)&&(identical(other.score, score) || other.score == score)&&(identical(other.sourceUrl, sourceUrl) || other.sourceUrl == sourceUrl)&&(identical(other.sectionTitle, sectionTitle) || other.sectionTitle == sectionTitle)&&(identical(other.isVerified, isVerified) || other.isVerified == isVerified)&&(identical(other.currentnessStatus, currentnessStatus) || other.currentnessStatus == currentnessStatus));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,document,section,provision,source,score,sourceUrl,sectionTitle,isVerified,currentnessStatus);

@override
String toString() {
  return 'Citation(document: $document, section: $section, provision: $provision, source: $source, score: $score, sourceUrl: $sourceUrl, sectionTitle: $sectionTitle, isVerified: $isVerified, currentnessStatus: $currentnessStatus)';
}


}

/// @nodoc
abstract mixin class $CitationCopyWith<$Res>  {
  factory $CitationCopyWith(Citation value, $Res Function(Citation) _then) = _$CitationCopyWithImpl;
@useResult
$Res call({
 String document, String section, String provision, String source, double score,@JsonKey(name: 'source_url') String? sourceUrl,@JsonKey(name: 'section_title') String? sectionTitle,@JsonKey(name: 'is_verified') bool isVerified,@JsonKey(name: 'currentness_status') String currentnessStatus
});




}
/// @nodoc
class _$CitationCopyWithImpl<$Res>
    implements $CitationCopyWith<$Res> {
  _$CitationCopyWithImpl(this._self, this._then);

  final Citation _self;
  final $Res Function(Citation) _then;

/// Create a copy of Citation
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? document = null,Object? section = null,Object? provision = null,Object? source = null,Object? score = null,Object? sourceUrl = freezed,Object? sectionTitle = freezed,Object? isVerified = null,Object? currentnessStatus = null,}) {
  return _then(Citation(
document: null == document ? _self.document : document // ignore: cast_nullable_to_non_nullable
as String,section: null == section ? _self.section : section // ignore: cast_nullable_to_non_nullable
as String,provision: null == provision ? _self.provision : provision // ignore: cast_nullable_to_non_nullable
as String,source: null == source ? _self.source : source // ignore: cast_nullable_to_non_nullable
as String,score: null == score ? _self.score : score // ignore: cast_nullable_to_non_nullable
as double,sourceUrl: freezed == sourceUrl ? _self.sourceUrl : sourceUrl // ignore: cast_nullable_to_non_nullable
as String?,sectionTitle: freezed == sectionTitle ? _self.sectionTitle : sectionTitle // ignore: cast_nullable_to_non_nullable
as String?,isVerified: null == isVerified ? _self.isVerified : isVerified // ignore: cast_nullable_to_non_nullable
as bool,currentnessStatus: null == currentnessStatus ? _self.currentnessStatus : currentnessStatus // ignore: cast_nullable_to_non_nullable
as String,
  ));
}

}


/// Adds pattern-matching-related methods to [Citation].
extension CitationPatterns on Citation {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _Citation value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _Citation() when $default != null:
return $default(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _Citation value)  $default,){
final _that = this;
switch (_that) {
case _Citation():
return $default(_that);}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _Citation value)?  $default,){
final _that = this;
switch (_that) {
case _Citation() when $default != null:
return $default(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( String document,  String section,  String provision,  String source,  double score, @JsonKey(name: 'source_url')  String? sourceUrl, @JsonKey(name: 'section_title')  String? sectionTitle, @JsonKey(name: 'is_verified')  bool isVerified, @JsonKey(name: 'currentness_status')  String currentnessStatus)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _Citation() when $default != null:
return $default(_that.document,_that.section,_that.provision,_that.source,_that.score,_that.sourceUrl,_that.sectionTitle,_that.isVerified,_that.currentnessStatus);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( String document,  String section,  String provision,  String source,  double score, @JsonKey(name: 'source_url')  String? sourceUrl, @JsonKey(name: 'section_title')  String? sectionTitle, @JsonKey(name: 'is_verified')  bool isVerified, @JsonKey(name: 'currentness_status')  String currentnessStatus)  $default,) {final _that = this;
switch (_that) {
case _Citation():
return $default(_that.document,_that.section,_that.provision,_that.source,_that.score,_that.sourceUrl,_that.sectionTitle,_that.isVerified,_that.currentnessStatus);}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( String document,  String section,  String provision,  String source,  double score, @JsonKey(name: 'source_url')  String? sourceUrl, @JsonKey(name: 'section_title')  String? sectionTitle, @JsonKey(name: 'is_verified')  bool isVerified, @JsonKey(name: 'currentness_status')  String currentnessStatus)?  $default,) {final _that = this;
switch (_that) {
case _Citation() when $default != null:
return $default(_that.document,_that.section,_that.provision,_that.source,_that.score,_that.sourceUrl,_that.sectionTitle,_that.isVerified,_that.currentnessStatus);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _Citation implements Citation {
  const _Citation({required this.document, required this.section, required this.provision, required this.source, required this.score, @JsonKey(name: 'source_url') this.sourceUrl, @JsonKey(name: 'section_title') this.sectionTitle, @JsonKey(name: 'is_verified') this.isVerified = false, @JsonKey(name: 'currentness_status') this.currentnessStatus = 'unknown'});
  factory _Citation.fromJson(Map<String, dynamic> json) => _$CitationFromJson(json);

@override final  String document;
@override final  String section;
@override final  String provision;
@override final  String source;
@override final  double score;
@override@JsonKey(name: 'source_url') final  String? sourceUrl;
@override@JsonKey(name: 'section_title') final  String? sectionTitle;
@override@JsonKey(name: 'is_verified') final  bool isVerified;
@override@JsonKey(name: 'currentness_status') final  String currentnessStatus;

/// Create a copy of Citation
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$CitationCopyWith<_Citation> get copyWith => __$CitationCopyWithImpl<_Citation>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$CitationToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _Citation&&(identical(other.document, document) || other.document == document)&&(identical(other.section, section) || other.section == section)&&(identical(other.provision, provision) || other.provision == provision)&&(identical(other.source, source) || other.source == source)&&(identical(other.score, score) || other.score == score)&&(identical(other.sourceUrl, sourceUrl) || other.sourceUrl == sourceUrl)&&(identical(other.sectionTitle, sectionTitle) || other.sectionTitle == sectionTitle)&&(identical(other.isVerified, isVerified) || other.isVerified == isVerified)&&(identical(other.currentnessStatus, currentnessStatus) || other.currentnessStatus == currentnessStatus));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,document,section,provision,source,score,sourceUrl,sectionTitle,isVerified,currentnessStatus);

@override
String toString() {
  return 'Citation(document: $document, section: $section, provision: $provision, source: $source, score: $score, sourceUrl: $sourceUrl, sectionTitle: $sectionTitle, isVerified: $isVerified, currentnessStatus: $currentnessStatus)';
}


}

/// @nodoc
abstract mixin class _$CitationCopyWith<$Res> implements $CitationCopyWith<$Res> {
  factory _$CitationCopyWith(_Citation value, $Res Function(_Citation) _then) = __$CitationCopyWithImpl;
@override @useResult
$Res call({
 String document, String section, String provision, String source, double score,@JsonKey(name: 'source_url') String? sourceUrl,@JsonKey(name: 'section_title') String? sectionTitle,@JsonKey(name: 'is_verified') bool isVerified,@JsonKey(name: 'currentness_status') String currentnessStatus
});




}
/// @nodoc
class __$CitationCopyWithImpl<$Res>
    implements _$CitationCopyWith<$Res> {
  __$CitationCopyWithImpl(this._self, this._then);

  final _Citation _self;
  final $Res Function(_Citation) _then;

/// Create a copy of Citation
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? document = null,Object? section = null,Object? provision = null,Object? source = null,Object? score = null,Object? sourceUrl = freezed,Object? sectionTitle = freezed,Object? isVerified = null,Object? currentnessStatus = null,}) {
  return _then(_Citation(
document: null == document ? _self.document : document // ignore: cast_nullable_to_non_nullable
as String,section: null == section ? _self.section : section // ignore: cast_nullable_to_non_nullable
as String,provision: null == provision ? _self.provision : provision // ignore: cast_nullable_to_non_nullable
as String,source: null == source ? _self.source : source // ignore: cast_nullable_to_non_nullable
as String,score: null == score ? _self.score : score // ignore: cast_nullable_to_non_nullable
as double,sourceUrl: freezed == sourceUrl ? _self.sourceUrl : sourceUrl // ignore: cast_nullable_to_non_nullable
as String?,sectionTitle: freezed == sectionTitle ? _self.sectionTitle : sectionTitle // ignore: cast_nullable_to_non_nullable
as String?,isVerified: null == isVerified ? _self.isVerified : isVerified // ignore: cast_nullable_to_non_nullable
as bool,currentnessStatus: null == currentnessStatus ? _self.currentnessStatus : currentnessStatus // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}


/// @nodoc
mixin _$FollowUpQuestion {

 String get question; String? get reason;
/// Create a copy of FollowUpQuestion
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$FollowUpQuestionCopyWith<FollowUpQuestion> get copyWith => _$FollowUpQuestionCopyWithImpl<FollowUpQuestion>(this as FollowUpQuestion, _$identity);

  /// Serializes this FollowUpQuestion to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is FollowUpQuestion&&(identical(other.question, question) || other.question == question)&&(identical(other.reason, reason) || other.reason == reason));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,question,reason);

@override
String toString() {
  return 'FollowUpQuestion(question: $question, reason: $reason)';
}


}

/// @nodoc
abstract mixin class $FollowUpQuestionCopyWith<$Res>  {
  factory $FollowUpQuestionCopyWith(FollowUpQuestion value, $Res Function(FollowUpQuestion) _then) = _$FollowUpQuestionCopyWithImpl;
@useResult
$Res call({
 String question, String? reason
});




}
/// @nodoc
class _$FollowUpQuestionCopyWithImpl<$Res>
    implements $FollowUpQuestionCopyWith<$Res> {
  _$FollowUpQuestionCopyWithImpl(this._self, this._then);

  final FollowUpQuestion _self;
  final $Res Function(FollowUpQuestion) _then;

/// Create a copy of FollowUpQuestion
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? question = null,Object? reason = freezed,}) {
  return _then(FollowUpQuestion(
question: null == question ? _self.question : question // ignore: cast_nullable_to_non_nullable
as String,reason: freezed == reason ? _self.reason : reason // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [FollowUpQuestion].
extension FollowUpQuestionPatterns on FollowUpQuestion {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _FollowUpQuestion value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _FollowUpQuestion() when $default != null:
return $default(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _FollowUpQuestion value)  $default,){
final _that = this;
switch (_that) {
case _FollowUpQuestion():
return $default(_that);}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _FollowUpQuestion value)?  $default,){
final _that = this;
switch (_that) {
case _FollowUpQuestion() when $default != null:
return $default(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( String question,  String? reason)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _FollowUpQuestion() when $default != null:
return $default(_that.question,_that.reason);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( String question,  String? reason)  $default,) {final _that = this;
switch (_that) {
case _FollowUpQuestion():
return $default(_that.question,_that.reason);}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( String question,  String? reason)?  $default,) {final _that = this;
switch (_that) {
case _FollowUpQuestion() when $default != null:
return $default(_that.question,_that.reason);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _FollowUpQuestion implements FollowUpQuestion {
  const _FollowUpQuestion({required this.question, this.reason});
  factory _FollowUpQuestion.fromJson(Map<String, dynamic> json) => _$FollowUpQuestionFromJson(json);

@override final  String question;
@override final  String? reason;

/// Create a copy of FollowUpQuestion
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$FollowUpQuestionCopyWith<_FollowUpQuestion> get copyWith => __$FollowUpQuestionCopyWithImpl<_FollowUpQuestion>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$FollowUpQuestionToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _FollowUpQuestion&&(identical(other.question, question) || other.question == question)&&(identical(other.reason, reason) || other.reason == reason));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,question,reason);

@override
String toString() {
  return 'FollowUpQuestion(question: $question, reason: $reason)';
}


}

/// @nodoc
abstract mixin class _$FollowUpQuestionCopyWith<$Res> implements $FollowUpQuestionCopyWith<$Res> {
  factory _$FollowUpQuestionCopyWith(_FollowUpQuestion value, $Res Function(_FollowUpQuestion) _then) = __$FollowUpQuestionCopyWithImpl;
@override @useResult
$Res call({
 String question, String? reason
});




}
/// @nodoc
class __$FollowUpQuestionCopyWithImpl<$Res>
    implements _$FollowUpQuestionCopyWith<$Res> {
  __$FollowUpQuestionCopyWithImpl(this._self, this._then);

  final _FollowUpQuestion _self;
  final $Res Function(_FollowUpQuestion) _then;

/// Create a copy of FollowUpQuestion
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? question = null,Object? reason = freezed,}) {
  return _then(_FollowUpQuestion(
question: null == question ? _self.question : question // ignore: cast_nullable_to_non_nullable
as String,reason: freezed == reason ? _self.reason : reason // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$ConversationResponse {

 String get answer; String get confidence; String get disclaimer; List<Citation> get citations;@JsonKey(name: 'follow_up_questions') List<FollowUpQuestion> get followUpQuestions;@JsonKey(name: 'needs_clarification') bool get needsClarification; String get status; bool get grounded; String get generation;@JsonKey(name: 'llm_provider') String? get llmProvider;@JsonKey(name: 'llm_model') String? get llmModel;@JsonKey(name: 'llm_error') String? get llmError;@JsonKey(name: 'retrieval_status') String? get retrievalStatus;@JsonKey(name: 'retrieval_total_found') int get retrievalTotalFound;@JsonKey(name: 'unverified_match_count') int get unverifiedMatchCount;@JsonKey(name: 'search_terms') List<String> get searchTerms; String? get audio;
/// Create a copy of ConversationResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ConversationResponseCopyWith<ConversationResponse> get copyWith => _$ConversationResponseCopyWithImpl<ConversationResponse>(this as ConversationResponse, _$identity);

  /// Serializes this ConversationResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ConversationResponse&&(identical(other.answer, answer) || other.answer == answer)&&(identical(other.confidence, confidence) || other.confidence == confidence)&&(identical(other.disclaimer, disclaimer) || other.disclaimer == disclaimer)&&const DeepCollectionEquality().equals(other.citations, citations)&&const DeepCollectionEquality().equals(other.followUpQuestions, followUpQuestions)&&(identical(other.needsClarification, needsClarification) || other.needsClarification == needsClarification)&&(identical(other.status, status) || other.status == status)&&(identical(other.grounded, grounded) || other.grounded == grounded)&&(identical(other.generation, generation) || other.generation == generation)&&(identical(other.llmProvider, llmProvider) || other.llmProvider == llmProvider)&&(identical(other.llmModel, llmModel) || other.llmModel == llmModel)&&(identical(other.llmError, llmError) || other.llmError == llmError)&&(identical(other.retrievalStatus, retrievalStatus) || other.retrievalStatus == retrievalStatus)&&(identical(other.retrievalTotalFound, retrievalTotalFound) || other.retrievalTotalFound == retrievalTotalFound)&&(identical(other.unverifiedMatchCount, unverifiedMatchCount) || other.unverifiedMatchCount == unverifiedMatchCount)&&const DeepCollectionEquality().equals(other.searchTerms, searchTerms)&&(identical(other.audio, audio) || other.audio == audio));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,answer,confidence,disclaimer,const DeepCollectionEquality().hash(citations),const DeepCollectionEquality().hash(followUpQuestions),needsClarification,status,grounded,generation,llmProvider,llmModel,llmError,retrievalStatus,retrievalTotalFound,unverifiedMatchCount,const DeepCollectionEquality().hash(searchTerms),audio);

@override
String toString() {
  return 'ConversationResponse(answer: $answer, confidence: $confidence, disclaimer: $disclaimer, citations: $citations, followUpQuestions: $followUpQuestions, needsClarification: $needsClarification, status: $status, grounded: $grounded, generation: $generation, llmProvider: $llmProvider, llmModel: $llmModel, llmError: $llmError, retrievalStatus: $retrievalStatus, retrievalTotalFound: $retrievalTotalFound, unverifiedMatchCount: $unverifiedMatchCount, searchTerms: $searchTerms, audio: $audio)';
}


}

/// @nodoc
abstract mixin class $ConversationResponseCopyWith<$Res>  {
  factory $ConversationResponseCopyWith(ConversationResponse value, $Res Function(ConversationResponse) _then) = _$ConversationResponseCopyWithImpl;
@useResult
$Res call({
 String answer, String confidence, String disclaimer, List<Citation> citations,@JsonKey(name: 'follow_up_questions') List<FollowUpQuestion> followUpQuestions,@JsonKey(name: 'needs_clarification') bool needsClarification, String status, bool grounded, String generation,@JsonKey(name: 'llm_provider') String? llmProvider,@JsonKey(name: 'llm_model') String? llmModel,@JsonKey(name: 'llm_error') String? llmError,@JsonKey(name: 'retrieval_status') String? retrievalStatus,@JsonKey(name: 'retrieval_total_found') int retrievalTotalFound,@JsonKey(name: 'unverified_match_count') int unverifiedMatchCount,@JsonKey(name: 'search_terms') List<String> searchTerms, String? audio
});




}
/// @nodoc
class _$ConversationResponseCopyWithImpl<$Res>
    implements $ConversationResponseCopyWith<$Res> {
  _$ConversationResponseCopyWithImpl(this._self, this._then);

  final ConversationResponse _self;
  final $Res Function(ConversationResponse) _then;

/// Create a copy of ConversationResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? answer = null,Object? confidence = null,Object? disclaimer = null,Object? citations = null,Object? followUpQuestions = null,Object? needsClarification = null,Object? status = null,Object? grounded = null,Object? generation = null,Object? llmProvider = freezed,Object? llmModel = freezed,Object? llmError = freezed,Object? retrievalStatus = freezed,Object? retrievalTotalFound = null,Object? unverifiedMatchCount = null,Object? searchTerms = null,Object? audio = freezed,}) {
  return _then(ConversationResponse(
answer: null == answer ? _self.answer : answer // ignore: cast_nullable_to_non_nullable
as String,confidence: null == confidence ? _self.confidence : confidence // ignore: cast_nullable_to_non_nullable
as String,disclaimer: null == disclaimer ? _self.disclaimer : disclaimer // ignore: cast_nullable_to_non_nullable
as String,citations: null == citations ? _self.citations : citations // ignore: cast_nullable_to_non_nullable
as List<Citation>,followUpQuestions: null == followUpQuestions ? _self.followUpQuestions : followUpQuestions // ignore: cast_nullable_to_non_nullable
as List<FollowUpQuestion>,needsClarification: null == needsClarification ? _self.needsClarification : needsClarification // ignore: cast_nullable_to_non_nullable
as bool,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,grounded: null == grounded ? _self.grounded : grounded // ignore: cast_nullable_to_non_nullable
as bool,generation: null == generation ? _self.generation : generation // ignore: cast_nullable_to_non_nullable
as String,llmProvider: freezed == llmProvider ? _self.llmProvider : llmProvider // ignore: cast_nullable_to_non_nullable
as String?,llmModel: freezed == llmModel ? _self.llmModel : llmModel // ignore: cast_nullable_to_non_nullable
as String?,llmError: freezed == llmError ? _self.llmError : llmError // ignore: cast_nullable_to_non_nullable
as String?,retrievalStatus: freezed == retrievalStatus ? _self.retrievalStatus : retrievalStatus // ignore: cast_nullable_to_non_nullable
as String?,retrievalTotalFound: null == retrievalTotalFound ? _self.retrievalTotalFound : retrievalTotalFound // ignore: cast_nullable_to_non_nullable
as int,unverifiedMatchCount: null == unverifiedMatchCount ? _self.unverifiedMatchCount : unverifiedMatchCount // ignore: cast_nullable_to_non_nullable
as int,searchTerms: null == searchTerms ? _self.searchTerms : searchTerms // ignore: cast_nullable_to_non_nullable
as List<String>,audio: freezed == audio ? _self.audio : audio // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [ConversationResponse].
extension ConversationResponsePatterns on ConversationResponse {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _ConversationResponse value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ConversationResponse() when $default != null:
return $default(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _ConversationResponse value)  $default,){
final _that = this;
switch (_that) {
case _ConversationResponse():
return $default(_that);}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _ConversationResponse value)?  $default,){
final _that = this;
switch (_that) {
case _ConversationResponse() when $default != null:
return $default(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( String answer,  String confidence,  String disclaimer,  List<Citation> citations, @JsonKey(name: 'follow_up_questions')  List<FollowUpQuestion> followUpQuestions, @JsonKey(name: 'needs_clarification')  bool needsClarification,  String status,  bool grounded,  String generation, @JsonKey(name: 'llm_provider')  String? llmProvider, @JsonKey(name: 'llm_model')  String? llmModel, @JsonKey(name: 'llm_error')  String? llmError, @JsonKey(name: 'retrieval_status')  String? retrievalStatus, @JsonKey(name: 'retrieval_total_found')  int retrievalTotalFound, @JsonKey(name: 'unverified_match_count')  int unverifiedMatchCount, @JsonKey(name: 'search_terms')  List<String> searchTerms,  String? audio)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ConversationResponse() when $default != null:
return $default(_that.answer,_that.confidence,_that.disclaimer,_that.citations,_that.followUpQuestions,_that.needsClarification,_that.status,_that.grounded,_that.generation,_that.llmProvider,_that.llmModel,_that.llmError,_that.retrievalStatus,_that.retrievalTotalFound,_that.unverifiedMatchCount,_that.searchTerms,_that.audio);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( String answer,  String confidence,  String disclaimer,  List<Citation> citations, @JsonKey(name: 'follow_up_questions')  List<FollowUpQuestion> followUpQuestions, @JsonKey(name: 'needs_clarification')  bool needsClarification,  String status,  bool grounded,  String generation, @JsonKey(name: 'llm_provider')  String? llmProvider, @JsonKey(name: 'llm_model')  String? llmModel, @JsonKey(name: 'llm_error')  String? llmError, @JsonKey(name: 'retrieval_status')  String? retrievalStatus, @JsonKey(name: 'retrieval_total_found')  int retrievalTotalFound, @JsonKey(name: 'unverified_match_count')  int unverifiedMatchCount, @JsonKey(name: 'search_terms')  List<String> searchTerms,  String? audio)  $default,) {final _that = this;
switch (_that) {
case _ConversationResponse():
return $default(_that.answer,_that.confidence,_that.disclaimer,_that.citations,_that.followUpQuestions,_that.needsClarification,_that.status,_that.grounded,_that.generation,_that.llmProvider,_that.llmModel,_that.llmError,_that.retrievalStatus,_that.retrievalTotalFound,_that.unverifiedMatchCount,_that.searchTerms,_that.audio);}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( String answer,  String confidence,  String disclaimer,  List<Citation> citations, @JsonKey(name: 'follow_up_questions')  List<FollowUpQuestion> followUpQuestions, @JsonKey(name: 'needs_clarification')  bool needsClarification,  String status,  bool grounded,  String generation, @JsonKey(name: 'llm_provider')  String? llmProvider, @JsonKey(name: 'llm_model')  String? llmModel, @JsonKey(name: 'llm_error')  String? llmError, @JsonKey(name: 'retrieval_status')  String? retrievalStatus, @JsonKey(name: 'retrieval_total_found')  int retrievalTotalFound, @JsonKey(name: 'unverified_match_count')  int unverifiedMatchCount, @JsonKey(name: 'search_terms')  List<String> searchTerms,  String? audio)?  $default,) {final _that = this;
switch (_that) {
case _ConversationResponse() when $default != null:
return $default(_that.answer,_that.confidence,_that.disclaimer,_that.citations,_that.followUpQuestions,_that.needsClarification,_that.status,_that.grounded,_that.generation,_that.llmProvider,_that.llmModel,_that.llmError,_that.retrievalStatus,_that.retrievalTotalFound,_that.unverifiedMatchCount,_that.searchTerms,_that.audio);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _ConversationResponse implements ConversationResponse {
  const _ConversationResponse({required this.answer, this.confidence = 'low', this.disclaimer = '',  List<Citation> citations = const <Citation>[], @JsonKey(name: 'follow_up_questions')  List<FollowUpQuestion> followUpQuestions = const <FollowUpQuestion>[], @JsonKey(name: 'needs_clarification') this.needsClarification = false, this.status = 'answered', this.grounded = false, this.generation = 'none', @JsonKey(name: 'llm_provider') this.llmProvider, @JsonKey(name: 'llm_model') this.llmModel, @JsonKey(name: 'llm_error') this.llmError, @JsonKey(name: 'retrieval_status') this.retrievalStatus, @JsonKey(name: 'retrieval_total_found') this.retrievalTotalFound = 0, @JsonKey(name: 'unverified_match_count') this.unverifiedMatchCount = 0, @JsonKey(name: 'search_terms')  List<String> searchTerms = const <String>[], this.audio}): _citations = citations,_followUpQuestions = followUpQuestions,_searchTerms = searchTerms;
  factory _ConversationResponse.fromJson(Map<String, dynamic> json) => _$ConversationResponseFromJson(json);

@override final  String answer;
@override@JsonKey() final  String confidence;
@override@JsonKey() final  String disclaimer;
 final  List<Citation> _citations;
@override@JsonKey() List<Citation> get citations {
  if (_citations is EqualUnmodifiableListView) return _citations;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_citations);
}

 final  List<FollowUpQuestion> _followUpQuestions;
@override@JsonKey(name: 'follow_up_questions') List<FollowUpQuestion> get followUpQuestions {
  if (_followUpQuestions is EqualUnmodifiableListView) return _followUpQuestions;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_followUpQuestions);
}

@override@JsonKey(name: 'needs_clarification') final  bool needsClarification;
@override@JsonKey() final  String status;
@override@JsonKey() final  bool grounded;
@override@JsonKey() final  String generation;
@override@JsonKey(name: 'llm_provider') final  String? llmProvider;
@override@JsonKey(name: 'llm_model') final  String? llmModel;
@override@JsonKey(name: 'llm_error') final  String? llmError;
@override@JsonKey(name: 'retrieval_status') final  String? retrievalStatus;
@override@JsonKey(name: 'retrieval_total_found') final  int retrievalTotalFound;
@override@JsonKey(name: 'unverified_match_count') final  int unverifiedMatchCount;
 final  List<String> _searchTerms;
@override@JsonKey(name: 'search_terms') List<String> get searchTerms {
  if (_searchTerms is EqualUnmodifiableListView) return _searchTerms;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_searchTerms);
}

@override final  String? audio;

/// Create a copy of ConversationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ConversationResponseCopyWith<_ConversationResponse> get copyWith => __$ConversationResponseCopyWithImpl<_ConversationResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ConversationResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ConversationResponse&&(identical(other.answer, answer) || other.answer == answer)&&(identical(other.confidence, confidence) || other.confidence == confidence)&&(identical(other.disclaimer, disclaimer) || other.disclaimer == disclaimer)&&const DeepCollectionEquality().equals(other._citations, _citations)&&const DeepCollectionEquality().equals(other._followUpQuestions, _followUpQuestions)&&(identical(other.needsClarification, needsClarification) || other.needsClarification == needsClarification)&&(identical(other.status, status) || other.status == status)&&(identical(other.grounded, grounded) || other.grounded == grounded)&&(identical(other.generation, generation) || other.generation == generation)&&(identical(other.llmProvider, llmProvider) || other.llmProvider == llmProvider)&&(identical(other.llmModel, llmModel) || other.llmModel == llmModel)&&(identical(other.llmError, llmError) || other.llmError == llmError)&&(identical(other.retrievalStatus, retrievalStatus) || other.retrievalStatus == retrievalStatus)&&(identical(other.retrievalTotalFound, retrievalTotalFound) || other.retrievalTotalFound == retrievalTotalFound)&&(identical(other.unverifiedMatchCount, unverifiedMatchCount) || other.unverifiedMatchCount == unverifiedMatchCount)&&const DeepCollectionEquality().equals(other._searchTerms, _searchTerms)&&(identical(other.audio, audio) || other.audio == audio));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,answer,confidence,disclaimer,const DeepCollectionEquality().hash(_citations),const DeepCollectionEquality().hash(_followUpQuestions),needsClarification,status,grounded,generation,llmProvider,llmModel,llmError,retrievalStatus,retrievalTotalFound,unverifiedMatchCount,const DeepCollectionEquality().hash(_searchTerms),audio);

@override
String toString() {
  return 'ConversationResponse(answer: $answer, confidence: $confidence, disclaimer: $disclaimer, citations: $citations, followUpQuestions: $followUpQuestions, needsClarification: $needsClarification, status: $status, grounded: $grounded, generation: $generation, llmProvider: $llmProvider, llmModel: $llmModel, llmError: $llmError, retrievalStatus: $retrievalStatus, retrievalTotalFound: $retrievalTotalFound, unverifiedMatchCount: $unverifiedMatchCount, searchTerms: $searchTerms, audio: $audio)';
}


}

/// @nodoc
abstract mixin class _$ConversationResponseCopyWith<$Res> implements $ConversationResponseCopyWith<$Res> {
  factory _$ConversationResponseCopyWith(_ConversationResponse value, $Res Function(_ConversationResponse) _then) = __$ConversationResponseCopyWithImpl;
@override @useResult
$Res call({
 String answer, String confidence, String disclaimer, List<Citation> citations,@JsonKey(name: 'follow_up_questions') List<FollowUpQuestion> followUpQuestions,@JsonKey(name: 'needs_clarification') bool needsClarification, String status, bool grounded, String generation,@JsonKey(name: 'llm_provider') String? llmProvider,@JsonKey(name: 'llm_model') String? llmModel,@JsonKey(name: 'llm_error') String? llmError,@JsonKey(name: 'retrieval_status') String? retrievalStatus,@JsonKey(name: 'retrieval_total_found') int retrievalTotalFound,@JsonKey(name: 'unverified_match_count') int unverifiedMatchCount,@JsonKey(name: 'search_terms') List<String> searchTerms, String? audio
});




}
/// @nodoc
class __$ConversationResponseCopyWithImpl<$Res>
    implements _$ConversationResponseCopyWith<$Res> {
  __$ConversationResponseCopyWithImpl(this._self, this._then);

  final _ConversationResponse _self;
  final $Res Function(_ConversationResponse) _then;

/// Create a copy of ConversationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? answer = null,Object? confidence = null,Object? disclaimer = null,Object? citations = null,Object? followUpQuestions = null,Object? needsClarification = null,Object? status = null,Object? grounded = null,Object? generation = null,Object? llmProvider = freezed,Object? llmModel = freezed,Object? llmError = freezed,Object? retrievalStatus = freezed,Object? retrievalTotalFound = null,Object? unverifiedMatchCount = null,Object? searchTerms = null,Object? audio = freezed,}) {
  return _then(_ConversationResponse(
answer: null == answer ? _self.answer : answer // ignore: cast_nullable_to_non_nullable
as String,confidence: null == confidence ? _self.confidence : confidence // ignore: cast_nullable_to_non_nullable
as String,disclaimer: null == disclaimer ? _self.disclaimer : disclaimer // ignore: cast_nullable_to_non_nullable
as String,citations: null == citations ? _self._citations : citations // ignore: cast_nullable_to_non_nullable
as List<Citation>,followUpQuestions: null == followUpQuestions ? _self._followUpQuestions : followUpQuestions // ignore: cast_nullable_to_non_nullable
as List<FollowUpQuestion>,needsClarification: null == needsClarification ? _self.needsClarification : needsClarification // ignore: cast_nullable_to_non_nullable
as bool,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,grounded: null == grounded ? _self.grounded : grounded // ignore: cast_nullable_to_non_nullable
as bool,generation: null == generation ? _self.generation : generation // ignore: cast_nullable_to_non_nullable
as String,llmProvider: freezed == llmProvider ? _self.llmProvider : llmProvider // ignore: cast_nullable_to_non_nullable
as String?,llmModel: freezed == llmModel ? _self.llmModel : llmModel // ignore: cast_nullable_to_non_nullable
as String?,llmError: freezed == llmError ? _self.llmError : llmError // ignore: cast_nullable_to_non_nullable
as String?,retrievalStatus: freezed == retrievalStatus ? _self.retrievalStatus : retrievalStatus // ignore: cast_nullable_to_non_nullable
as String?,retrievalTotalFound: null == retrievalTotalFound ? _self.retrievalTotalFound : retrievalTotalFound // ignore: cast_nullable_to_non_nullable
as int,unverifiedMatchCount: null == unverifiedMatchCount ? _self.unverifiedMatchCount : unverifiedMatchCount // ignore: cast_nullable_to_non_nullable
as int,searchTerms: null == searchTerms ? _self._searchTerms : searchTerms // ignore: cast_nullable_to_non_nullable
as List<String>,audio: freezed == audio ? _self.audio : audio // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$ConversationStatus {

@JsonKey(name: 'session_id') String get sessionId; String get status; String get language;@JsonKey(name: 'message_count') int get messageCount;@JsonKey(name: 'started_at') String? get startedAt; List<ConversationMessage> get messages;
/// Create a copy of ConversationStatus
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ConversationStatusCopyWith<ConversationStatus> get copyWith => _$ConversationStatusCopyWithImpl<ConversationStatus>(this as ConversationStatus, _$identity);

  /// Serializes this ConversationStatus to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ConversationStatus&&(identical(other.sessionId, sessionId) || other.sessionId == sessionId)&&(identical(other.status, status) || other.status == status)&&(identical(other.language, language) || other.language == language)&&(identical(other.messageCount, messageCount) || other.messageCount == messageCount)&&(identical(other.startedAt, startedAt) || other.startedAt == startedAt)&&const DeepCollectionEquality().equals(other.messages, messages));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,sessionId,status,language,messageCount,startedAt,const DeepCollectionEquality().hash(messages));

@override
String toString() {
  return 'ConversationStatus(sessionId: $sessionId, status: $status, language: $language, messageCount: $messageCount, startedAt: $startedAt, messages: $messages)';
}


}

/// @nodoc
abstract mixin class $ConversationStatusCopyWith<$Res>  {
  factory $ConversationStatusCopyWith(ConversationStatus value, $Res Function(ConversationStatus) _then) = _$ConversationStatusCopyWithImpl;
@useResult
$Res call({
@JsonKey(name: 'session_id') String sessionId, String status, String language,@JsonKey(name: 'message_count') int messageCount,@JsonKey(name: 'started_at') String? startedAt, List<ConversationMessage> messages
});




}
/// @nodoc
class _$ConversationStatusCopyWithImpl<$Res>
    implements $ConversationStatusCopyWith<$Res> {
  _$ConversationStatusCopyWithImpl(this._self, this._then);

  final ConversationStatus _self;
  final $Res Function(ConversationStatus) _then;

/// Create a copy of ConversationStatus
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? sessionId = null,Object? status = null,Object? language = null,Object? messageCount = null,Object? startedAt = freezed,Object? messages = null,}) {
  return _then(ConversationStatus(
sessionId: null == sessionId ? _self.sessionId : sessionId // ignore: cast_nullable_to_non_nullable
as String,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,language: null == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as String,messageCount: null == messageCount ? _self.messageCount : messageCount // ignore: cast_nullable_to_non_nullable
as int,startedAt: freezed == startedAt ? _self.startedAt : startedAt // ignore: cast_nullable_to_non_nullable
as String?,messages: null == messages ? _self.messages : messages // ignore: cast_nullable_to_non_nullable
as List<ConversationMessage>,
  ));
}

}


/// Adds pattern-matching-related methods to [ConversationStatus].
extension ConversationStatusPatterns on ConversationStatus {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _ConversationStatus value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ConversationStatus() when $default != null:
return $default(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _ConversationStatus value)  $default,){
final _that = this;
switch (_that) {
case _ConversationStatus():
return $default(_that);}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _ConversationStatus value)?  $default,){
final _that = this;
switch (_that) {
case _ConversationStatus() when $default != null:
return $default(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function(@JsonKey(name: 'session_id')  String sessionId,  String status,  String language, @JsonKey(name: 'message_count')  int messageCount, @JsonKey(name: 'started_at')  String? startedAt,  List<ConversationMessage> messages)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ConversationStatus() when $default != null:
return $default(_that.sessionId,_that.status,_that.language,_that.messageCount,_that.startedAt,_that.messages);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function(@JsonKey(name: 'session_id')  String sessionId,  String status,  String language, @JsonKey(name: 'message_count')  int messageCount, @JsonKey(name: 'started_at')  String? startedAt,  List<ConversationMessage> messages)  $default,) {final _that = this;
switch (_that) {
case _ConversationStatus():
return $default(_that.sessionId,_that.status,_that.language,_that.messageCount,_that.startedAt,_that.messages);}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function(@JsonKey(name: 'session_id')  String sessionId,  String status,  String language, @JsonKey(name: 'message_count')  int messageCount, @JsonKey(name: 'started_at')  String? startedAt,  List<ConversationMessage> messages)?  $default,) {final _that = this;
switch (_that) {
case _ConversationStatus() when $default != null:
return $default(_that.sessionId,_that.status,_that.language,_that.messageCount,_that.startedAt,_that.messages);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _ConversationStatus implements ConversationStatus {
  const _ConversationStatus({@JsonKey(name: 'session_id') required this.sessionId, required this.status, this.language = 'nepali', @JsonKey(name: 'message_count') this.messageCount = 0, @JsonKey(name: 'started_at') this.startedAt,  List<ConversationMessage> messages = const <ConversationMessage>[]}): _messages = messages;
  factory _ConversationStatus.fromJson(Map<String, dynamic> json) => _$ConversationStatusFromJson(json);

@override@JsonKey(name: 'session_id') final  String sessionId;
@override final  String status;
@override@JsonKey() final  String language;
@override@JsonKey(name: 'message_count') final  int messageCount;
@override@JsonKey(name: 'started_at') final  String? startedAt;
 final  List<ConversationMessage> _messages;
@override@JsonKey() List<ConversationMessage> get messages {
  if (_messages is EqualUnmodifiableListView) return _messages;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_messages);
}


/// Create a copy of ConversationStatus
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ConversationStatusCopyWith<_ConversationStatus> get copyWith => __$ConversationStatusCopyWithImpl<_ConversationStatus>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ConversationStatusToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ConversationStatus&&(identical(other.sessionId, sessionId) || other.sessionId == sessionId)&&(identical(other.status, status) || other.status == status)&&(identical(other.language, language) || other.language == language)&&(identical(other.messageCount, messageCount) || other.messageCount == messageCount)&&(identical(other.startedAt, startedAt) || other.startedAt == startedAt)&&const DeepCollectionEquality().equals(other._messages, _messages));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,sessionId,status,language,messageCount,startedAt,const DeepCollectionEquality().hash(_messages));

@override
String toString() {
  return 'ConversationStatus(sessionId: $sessionId, status: $status, language: $language, messageCount: $messageCount, startedAt: $startedAt, messages: $messages)';
}


}

/// @nodoc
abstract mixin class _$ConversationStatusCopyWith<$Res> implements $ConversationStatusCopyWith<$Res> {
  factory _$ConversationStatusCopyWith(_ConversationStatus value, $Res Function(_ConversationStatus) _then) = __$ConversationStatusCopyWithImpl;
@override @useResult
$Res call({
@JsonKey(name: 'session_id') String sessionId, String status, String language,@JsonKey(name: 'message_count') int messageCount,@JsonKey(name: 'started_at') String? startedAt, List<ConversationMessage> messages
});




}
/// @nodoc
class __$ConversationStatusCopyWithImpl<$Res>
    implements _$ConversationStatusCopyWith<$Res> {
  __$ConversationStatusCopyWithImpl(this._self, this._then);

  final _ConversationStatus _self;
  final $Res Function(_ConversationStatus) _then;

/// Create a copy of ConversationStatus
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? sessionId = null,Object? status = null,Object? language = null,Object? messageCount = null,Object? startedAt = freezed,Object? messages = null,}) {
  return _then(_ConversationStatus(
sessionId: null == sessionId ? _self.sessionId : sessionId // ignore: cast_nullable_to_non_nullable
as String,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,language: null == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as String,messageCount: null == messageCount ? _self.messageCount : messageCount // ignore: cast_nullable_to_non_nullable
as int,startedAt: freezed == startedAt ? _self.startedAt : startedAt // ignore: cast_nullable_to_non_nullable
as String?,messages: null == messages ? _self._messages : messages // ignore: cast_nullable_to_non_nullable
as List<ConversationMessage>,
  ));
}


}

// dart format on
