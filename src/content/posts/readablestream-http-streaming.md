---
title: 'ReadableStream으로 http요청 Streaming 하기'
description: 'fetch의 한계라던 업로드 진행률이 ky에 어떻게 추가됐는지 — duplex: half와 ReadableStream의 원리, 그리고 아직 남은 한계를 파본 기록.'
pubDate: 2025-05-26
tags: ['fetch', 'stream', 'ky']
draft: false
---

몇 개월 전 만해도 업로드 progress를 구현하려면 fetch로는 방법이 없었다. 웹소켓을 사용하든 폴링을 하든 서버에서 응답을 받아서 보여주거나 xml을 사용해서 업로드용 api request를 만들어야 했다. 근데 얼마 전에 ky에 onUploadProgress가 추가되었다!  
onDownloadProgress는 있었지만 분명히 fetch기반 라이브러리의 한계로 onUploadProgress는 없었다.

분명히 fetch의 한계라고 했는데 어떻게 구현한걸까?

## ky의 onDownloadProgress는 어떻게 구현했을까

1. ky의 onDownloadProgress는 어떻게 구현했을까

ky는 fetch api기반의 http 클라이언트 라이브러리이다. 이 라이브러리에는 이미 onDownloadProgress 옵션이 구현되어 있었다.  
얼마나 다운로드가 완료되었는지 진행률을 클라이언트 측에서 다룰 수 있다. 소스코드의 핵심 부분을 보면

```typescript
if (ky._options.onDownloadProgress) {
	...
	return streamResponse(response.clone(), ky._options.onDownloadProgress);
}
```

사용자가 onDownloadProgress옵션을 사용하면 streamResponse를 리턴한다. 이름에서 알 수 있듯이, 서버의 response를 복사해서 stream으로 만든 response를 반환한다. 그리고 사용자의 콜백을 전달한다.

```typescript
export const streamResponse = (
  response: Response,
  onDownloadProgress: Options["onDownloadProgress"]
) => {
  return new Response(
    new ReadableStream({
      async start(controller) {
        ...
        if (onDownloadProgress) {
          onDownloadProgress({ percent: 0, transferredBytes: 0, totalBytes },
          new Uint8Array());
        }

        async function read() {
          if (onDownloadProgress) {
          ...
          onDownloadProgress({ percent, transferredBytes, totalBytes },value)}
          ...
        }
        ...
      },
    }),
    {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    }
  );
};
```

Response를 가로채서 new Response객체를 반환하면서 결괏값을 스트림으로 바꿔준다. 그리고 스트림이 읽힐 때마다 onDownloadProgress를 호출하며 진행률을 인자로 넣어준다. 간단하다.  
정리하자면 fetch를 통해 받은 응답은 스트림으로 변경해서 받을 수 있기 때문에 다운로드 진행률을 추적할 수 있다.

## 왜 onUploadProgress는 지원하지 않았을까

2. 왜 onUploadProgress는 지원하지 않았을까?

비슷한 onUploadProgress도 비슷하게 구현을 하면 될 것 같지만 안된다. 아니 안 됐었다. 왜냐하면 초기 fetch는 보안 및 브라우저 구현상의 제약으로 인해 Request의 body에 Stream을 사용할 수 없었다. Request에 데이터를 보내기 위해서는 전체 body를 미리 준비해야 했다. 즉, 메모리에 한 번에 올려야 한다. formData를 미리 다 만들어놓는 것처럼..

## Request에 Stream 지원: duplex: 'half'의 등장

3. Request에 Stream 지원: duplex: 'half'의 등장

2022년 무렵, fetch 사양에 duplex: 'half' 옵션이 실험적으로 도입되면서, Request.body에 ReadableStream을 사용할 수 있게 되었다. 크롬 버전은 105 버전부터 지원이 된다. 이 옵션을 명시함으로써 우리는 비동기적으로 데이터를 업로드할 수 있고, 이에 따라 진행률을 추적하는 것도 가능해졌다.

5. 스트림을 활용한 progress 추적 구현 예시

```typescript
// 출처: https://developer.chrome.com/docs/capabilities/web-apis/fetch-streaming-requests
function wait(milliseconds) {
  return new Promise(resolve => setTimeout(resolve, milliseconds));
}

const stream = new ReadableStream({
  async start(controller) {
    await wait(1000);
    controller.enqueue('This ');
    await wait(1000);
    controller.enqueue('is ');
    await wait(1000);
    controller.enqueue('a ');
    await wait(1000);
    controller.enqueue('slow ');
    await wait(1000);
    controller.enqueue('request.');
    controller.close();
  },
}).pipeThrough(new TextEncoderStream());

fetch(url, {
  method: 'POST',
  headers: {'Content-Type': 'text/plain'},
  body: stream,
  duplex: 'half',
});
```

fetch로 post 요청 시 body에 stream을 담았다. 역시 해보니 어색하다. 완성된 데이터가 아닌데, 보낼 수 있다.

## Ky는 어떻게 구현했을까

6. Ky는 어떻게 구현했을까?

ky는 라이브러리이기 때문에 복잡한 스트림 과정을 추상화하고 onDownloadProgress와 동일한 인터페이스를 제공하여 일관된 경험을 제공했다.

```typescript
if (this._options.onUploadProgress) {
	if(typeof this._options.onUploadProgress !== "function"){
    	// 에러 반환
    }
    if(!supportsRequestStreams){
    	// 에러 반환 => supportsRequestStreams는 뒤에서 설명	
    }
    
    const originalBody = this.request.body;
    if (originalBody) {
        this.request = streamRequest(
            this.request,
            this._options.onUploadProgress,
        );
    }
```

요청을 보내기 전에 this.request를 stream데이터가 담긴 Request로 교체한다.  
그리고 fetch 할 때 실제로 this.request를 인자로 호출한다.

```typescript
export const streamRequest = (request, onUploadProgress) => {
  return new Request(request, {
    // @ts-expect-error - Types are outdated.
    duplex: "half",
    body: new ReadableStream({
      async start(controller) {
        ...
        async function read() {
          const { done, value } = await reader.read();
          if (done) {
            if (onUploadProgress) {
              onUploadProgress(
                {
                  percent: 1,
                  transferredBytes,
                  totalBytes: Math.max(totalBytes, transferredBytes),
                },
                new Uint8Array()
              );
            }
            ...
          }
          ...         
          if (onUploadProgress) {
            onUploadProgress(
              {
                percent: Number(percent.toFixed(2)),
                transferredBytes,
                totalBytes,
              },
              value
            );
          }
          ...
        },
      }),
  });
}
```

결국 리턴하는 new Request가 this.request가 되는데, 이 새로운 객체인 Request는 duplex:"half"속성을 가지고 있고, body에는 ReadableStream이 들어간다. 이 스트림은 read()가 호출될 때마다 사용자가 콜백으로 전달한 onUploadProgress를 호출하며 현재 전송된 바이트의 양을 퍼센트 단위로 넣어준다. done이 true가 되면 단순히 종료시키는 streamResponse와 달리 100% 전송되었다고 한번 콜백을 호출하고 닫아준다.

duplex:"half" 부분에 // @ts-expect-error - Types are outdated 주석이 있다.

아직 @types/node 도 업데이트 되지 않아서 이 주석이 없으면 이상한 거 넣지 말라는 에러가 뜬다.

그리고 처음에도 언급했듯, 크롬 105 버전 이상에서만 동작한다. 우리의 유저는 크롬을 업데이트하지 않을 확률이 아주 크기 때문에 이 기능을 사용하지 못할 수도 있다. 현재 환경이 request에 stream을 보내는 게 가능한지 확인해야 한다.

## Ky사용 시 에러처리 필요

7. Ky사용 시 에러처리 필요

여기서 위에 잠깐 나왔던 supportsRequestrStreams가 필요해진다.

```typescript
// 출처 - https://developer.chrome.com/docs/capabilities/web-apis/fetch-streaming-requests

const supportsRequestStreams = (() => {
  let duplexAccessed = false;

  const hasContentType = new Request('', {
    body: new ReadableStream(),
    method: 'POST',
    get duplex() {
      duplexAccessed = true;
      return 'half';
    },
  }).headers.has('Content-Type');

  return duplexAccessed && !hasContentType;
})();
```

현재 환경이 stream Request를 지원하는지 판단하는 코드이다.

일단 new Request객체를 다짜고짜 만들어보고 body에 다짜고짜 ReadableStream을 넣어본다. 만약 브라우저가 특정 유형을 지원하지 않으면 객체 내부적으로 toString()을 호출한다. 즉, 위 코드가 동작하지 않는 환경이면 body: "[object ReadableStream]"이 들어갈 것이다. 그리고 body에 문자열이 들어가면 Content-Type 헤더가 text/plain;charset=UTF-8로 설정된다. 그러므로 headers.has('Content-Type')에서 값이 나오면 이 환경은 Request에 ReadableStream을 제공하지 않는구나!로 판단할 수 있다는 뜻이다.

다시 ky코드로 돌아가면

```typescript
if (!supportsRequestStreams) {
  throw new Error(
    "Request streams are not supported in your environment. The `duplex` option for `Request` is not available.",
  );
}
```

환경에서 지원하지 않으면 그냥 에러를 던진다.

그러므로 프론트엔드 개발자는 유저가 구버전의 브라우저를 사용하는 경우를 생각해서 에러가 발생할 상황에 대한 에러처리를 해줘야 한다.

어떻게 해줄까? 구형사용자는 xml로 구현해 줄까? 그럼 그냥 xml로 하는 게 편하지 않나..?

여기까지 보니 아직은 프로덕트에 도입하기엔 시기가 이르다는 판단이 들었다.

## duplex: 'half'란?

8. duplex: 'half'란?

duplex: 'half'는 업로드 시 Stream을 사용하는 기능을 활성화하기 위한 옵션이다. 'half'란 이름에서 알 수 있듯이, **한 방향(업로드 또는 다운로드)** 만 스트리밍 가능하다는 의미이다. 즉, 완전한 duplex(양방향 스트림) 통신은 아니다. 문서에서 보면 알 수 있듯이, http는 요청을 보내는 중에도 응답을 받을 수 있도록 설계되어 있다. 근데 이 사실이 너무 알려지지 않아서 서버나 브라우저에서 지원되지 않는다. 즉, 아직은 모든 요청을 다 보내기 전까진 응답을 받을 수 없다는 뜻이다. 이것이 half duplex이다. 근데 http가 요청 중에도 응답을 받을 수 있도록 설계되어 있다면 나중에는 언젠가 스트림을 보내는 중간에 응답을 받는 것도 구현이 되지 않을까? 기대된다.

## 한계: 에러 처리 불가와 버퍼링

9. 한계: 반이중 통신으로 인한 에러 처리 불가

위에서 말했듯, half duplex는 업로드 중 서버에서 에러를 응답해도, 클라이언트는 이 응답을 읽기 전에 업로드를 끝내야 한다. 이는 서버와의 실시간 상호작용에 한계를 만든다. 예를 들어, 서버가 업로드 파일에서 에러를 발견하거나 의도적인 exception을 보내주고 싶어서 특정 시점에 업로드를 중단시키려 해도 클라이언트는 계속 전송하게 된다. 그럼 대용량파일 업로드를 중간에 끊지 못하고 100%가 될 때까지 모든 청크를 보내야만 한다. 1%처리했을 때 익셉션이 터졌는데, 유저는 100%까지 기다려야 그 결과를 볼 수 있다는 것이다.

10. 한계: 인프라의 뒷받침 필요: 버퍼링

또 다른 한계로는 인프라의 뒷받침이 필요하다는 것이다.  
[https://pungwa.tistory.com/225](https://pungwa.tistory.com/225)

위 블로그는 내가 nextjs로 ui를 스트리밍 방식으로 그리고자 했을때 트러블 슈팅 했던 기록이다. 간단하게 정리하자면, nextjs서버에서 서버컴포넌트 ui랜더링을 한 뒤에 클라이언트로 스트림을 보내서 ui를 그린다. 장점은 정적인 화면에 대해 서버에서만 한번 랜더링함으로써 유저의 네트워크 환경에 상관없이 빠른 랜더링을 할 수 있고, cdn 등을 활용해 로딩속도를 획기적으로 줄일 수 있다. 개발을 완료하고 웹서버를 nginx로 세팅해서 배포했는데 스트림데이터를 받아서 fallback을 그리지 못하고 완성된 화면이 나올 때까지 흰 화면이 나오다가 스켈레톤을 생략하고 완성된 화면을 그렸다. 이유는 웹서버가 모든 응답을 버퍼링 하기 때문에 소스코드에서 스트림으로 데이터를 내려도 클라이언트까지 응답이 가지 않는다. Request도 마찬가지이다. 만약 클라이언트에서 서버까지 프록시를 거치게 된다면 어디서 버퍼링을 할지 모른다. 모든 인프라가 버퍼를 제거해야 한다. 근데 nginx 같은 인프라에서 기본으로 버퍼를 사용하는 이유가 있다. 보안 이슈도 있는 것으로 알고 있는데, 이런 것들과 트레이드오프 했을 때도 과연 Request ReadableStream이 유효할지 판단은 필요하다.

## 가능한 해결 방법과 기대 사항

11. 가능한 해결 방법: SSE 또는 WebSocket

이러한 한계를 극복하려면 서버와 클라이언트 간 양방향 통신이 가능해야 한다. 이를 위해 다음과 같은 기술을 고려할 수 있다:

- **Server-Sent Events (SSE)**: 서버에서 클라이언트로 일방향 메시지를 보낼 수 있다.

- **WebSocket**: 클라이언트와 서버 간에 완전한 양방향 실시간 통신을 제공한다. 요청-응답의 형태가 아니므로 유연한 통신 구조가 가능하다.

무슨 말이냐면 Request로 Stream을 보내면서, 동시에 웹소켓을 뚫어서 익셉션이나 에러를 받는 채널을 동시에 유지하라는 말이다. 그러면 서버에서 보내는 익셉션을 포착해서 Request를 중단하라는 것이다. SSE도 마찬가지. 아직 한계가 많다는 것이다.

12. 기대 사항: 브라우저에서 duplex: 'full' 지원될까?

현재는 duplex: 'half'만 가능하지만, 향후에는 duplex: 'full' 옵션이 브라우저 사양에 포함될 가능성도 있다. 이를 통해 WebSocket처럼 브라우저의 fetch API만으로 양방향 실시간 통신이 가능해지면, HTTP 기반 통신의 유연성과 실시간성이 모두 확보될 수 있다. 이는 대용량 업로드, 스트리밍 기반 애플리케이션 등에 큰 혁신을 가져올 수 있겠다!
