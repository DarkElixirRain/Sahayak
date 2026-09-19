// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'chat_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(ChatNotifier)
final chatProvider = ChatNotifierFamily._();

final class ChatNotifierProvider
    extends $AsyncNotifierProvider<ChatNotifier, ChatUiState> {
  ChatNotifierProvider._({
    required ChatNotifierFamily super.from,
    required String super.argument,
  }) : super(
         retry: null,
         name: r'chatProvider',
         isAutoDispose: true,
         dependencies: null,
         $allTransitiveDependencies: null,
       );

  @override
  String debugGetCreateSourceHash() => _$chatNotifierHash();

  @override
  String toString() {
    return r'chatProvider'
        ''
        '($argument)';
  }

  @$internal
  @override
  ChatNotifier create() => ChatNotifier();

  @override
  bool operator ==(Object other) {
    return other is ChatNotifierProvider && other.argument == argument;
  }

  @override
  int get hashCode {
    return argument.hashCode;
  }
}

String _$chatNotifierHash() => r'b6bad4990ab866cab93b80b8f78509e33442a471';

final class ChatNotifierFamily extends $Family
    with
        $ClassFamilyOverride<
          ChatNotifier,
          AsyncValue<ChatUiState>,
          ChatUiState,
          FutureOr<ChatUiState>,
          String
        > {
  ChatNotifierFamily._()
    : super(
        retry: null,
        name: r'chatProvider',
        dependencies: null,
        $allTransitiveDependencies: null,
        isAutoDispose: true,
      );

  ChatNotifierProvider call(String sessionId) =>
      ChatNotifierProvider._(argument: sessionId, from: this);

  @override
  String toString() => r'chatProvider';
}

abstract class _$ChatNotifier extends $AsyncNotifier<ChatUiState> {
  late final _$args = ref.$arg as String;
  String get sessionId => _$args;

  FutureOr<ChatUiState> build(String sessionId);
  @$mustCallSuper
  @override
  WhenComplete runBuild() {
    final ref = this.ref as $Ref<AsyncValue<ChatUiState>, ChatUiState>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<AsyncValue<ChatUiState>, ChatUiState>,
              AsyncValue<ChatUiState>,
              Object?,
              Object?
            >;
    return element.handleCreate(ref, () => build(_$args));
  }
}
