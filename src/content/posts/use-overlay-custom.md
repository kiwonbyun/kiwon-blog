---
title: '토스의 useOverlay를 분석하고 나에게 필요한 수준으로 커스텀하기'
description: '토스 useOverlay의 close와 exit이 왜 나뉘어 있는지 뜯어보고, 모달 ui와 애니메이션을 기본으로 넣은 훅으로 다시 만든 기록.'
pubDate: 2025-02-09
tags: ['react', '오버레이', '모달']
---

[https://www.slash.page/ko/libraries/react/use-overlay/src/useOverlay.i18n](https://www.slash.page/ko/libraries/react/use-overlay/src/useOverlay.i18n)

이것은 토스에서 만든 오버레이를 선언적으로 다룰 수 있는 훅이다.

useOverlay훅은 ui를 제공하지 않고 호출시점에 오버레이가 보이는(isOpen) 상태를 주입해 주고, 보이지 않게 해주는 함수를 제공하는 훅이다. 즉, useOverlay를 사용하더라도 ui는 직접 만들어야 한다. 그 ui를 모달로 할지, 바텀시트로 할지는 개발자가 결정하면 된다.

이 글은 useOverlay를 사용하는 방법을 소개하는 글이나 코드를 읽어보는 글이 아니다.

useOverlay를 작성한 개발자들이 어떤 생각을 했는지, 나에게는 어떤 기능이 필요했는지, 그래서 어떻게 커스텀했는지 정리하는 글이다.

## close와 exit, 둘 중 어느 것을 호출해도 닫힌다

이 라이브러리를 처음 보고 가능 의문이 들었던 점은 close함수와 exit함수 두 가지가 있는데, 둘 중 어느 것을 호출해도 모달이 잘 닫힌다는 것이다. 모든 소스코드는 직접 github에서 보시면 됩니다!

```javascript
export function useOverlay() {
  ...

  useEffect(() => {
    return () => {
      if (exitOnUnmount) {
        unmount(id);
      }
    };
  }, [exitOnUnmount, id, unmount]);

  return useMemo(
    () => ({
      open: (overlayElement: CreateOverlayElement) => {
        mount(
          id,
          <OverlayController
           ...
          />
        );
      },
      close: () => {
        overlayRef.current?.close();
      },
      exit: () => {
        unmount(id);
      },
    }),
    [id, mount, unmount]
  );
}
```

요약하자면 useOverlay훅은 open, close, exit함수를 리턴한다. 여기서 close와 exit의 구분이 필요한데, exit은 unmount를 호출한다.

```javascript
  const [overlayById, setOverlayById] = useState<Map<string, ReactNode>>(new Map());

  const mount = useCallback((id: string, element: ReactNode) => {
    setOverlayById(overlayById => {
      const cloned = new Map(overlayById);
      cloned.set(id, element);
      return cloned;
    });
  }, []);

  const unmount = useCallback((id: string) => {
    setOverlayById(overlayById => {
      const cloned = new Map(overlayById);
      cloned.delete(id);
      return cloned;
    });
  }, []);
```

mount, unmount함수는 OverlayProvider로 내려오는 함수인데, 상태에 올리고 없애는 역할을 한다. 타입을 보면 알 수 있듯이, 오버레이 ui(모달이든 바텀시트든,,)가 Map객체의 값으로 관리되는 상태이다. 즉, mount는 리액트 엘리먼트를 메모리에 올리고 unmount는 메모리에서 제거하는 함수이다.

그럼 exit은 리액트 엘리먼트를 메모리에서 지우는 함수다. 오버레이 ui가 꺼지면 당연히 메모리에서 지우면 되니까 exit만 호출해도 될 것 같은데, close는 뭘까??

```javascript
close: () => {
	overlayRef.current?.close();
},
```

close는 ref에 할당된 엘리먼트의 close를 호출한다. ref에 무엇이 할당되었는지 보면

```javascript
export const OverlayController = forwardRef(function OverlayController(
  { overlayElement: OverlayElement, onExit }: Props,
  ref: Ref<OverlayControlRef>
) {
  const [isOpenOverlay, setIsOpenOverlay] = useState(false);

  const handleOverlayClose = useCallback(() => setIsOpenOverlay(false), []);

  useImperativeHandle(
    ref,
    () => {
      return { close: handleOverlayClose };
    },
    [handleOverlayClose]
  );

  useEffect(() => {
    // NOTE: requestAnimationFrame이 없으면 가끔 Open 애니메이션이 실행되지 않는다.
    requestAnimationFrame(() => {
      setIsOpenOverlay(true);
    });
  }, []);

  return <OverlayElement isOpen={isOpenOverlay} close={handleOverlayClose} exit={onExit} />;
});
```

open함수의 콜백으로 호출한 리액트 엘리먼트의 close를 호출한다. handleOverlayClose가 useImperativeHandle훅으로 ref에 등록되는데, 자식에 등록된 핸들러를 상위 컴포넌트에서 호출할 수 있게 된다.  
close함수는 뭔가 하니.. 단순히 isOpenOverlay상태를 false로 만들어서 visible상태를 안 보이게 만들어주는 함수이다.

이 함수는 unmount를 호출하지 않는다. 그러므로 사용자가 ui를 구현할때 이 isOpen 상태에 따라 visible처리를 적절히 해주지 않으면 계속 마운트 되어있는 상태이니 눈에 보이게 될 것이다. 그럼 왜 close와 exit을 구분하여 만들었나?

## 왜 close와 exit을 구분했나

공식문서에 힌트가 있는데

```javascript
type CreateOverlayElement = (props: {
  // open()을 호출했을 때 isOpen이 true로 바뀝니다. 이 값을 이용해서 Overlay에 띄울 컴포넌트의 open 상태를 관리합니다.
  isOpen: boolean;
  // 이 함수가 호출되면 isOpen이 false로 바뀝니다. 주로 Overlay로 띄울 컴포넌트의 onClose 함수에 이 함수를 주입합니다.
  close: () => void;
  // 이 함수가 호출되면 해당 Overlay가 unmount됩니다.
  // close와 exit이 분리되어 있는 이유는 Overlay를 닫으면서 fade-out 애니메이션을 주고 싶을 때 close와 동시에 unmount시켜버리면 애니메이션이 먹히기 때문입니다.
  exit: () => void;
}) => JSX.Element;
```

그렇다. exit을 호출하면 즉시 메모리에서 사라지기 때문에 fade-out같은 애니메이션을 보여줄 겨를도 없이 화면에서 사라진다.

등장할 때는 mount하든, isOpenOverlay로 등장하든 동일하게 애니메이션이 동작하지만 사라질 때는 애니메이션을 보여줄 경우에는 즉시 언마운트 시키면 안 된다.

즉, 토스에서 제공한 useOverlay는 ui에 대한 통제권을 완전히 사용자에게 넘긴다. 이름에서도 알 수 있듯이 이것은 useModal이나 useBottomSheet가 아니라 useOverlay다. ui로 modal을 제공할지 bottomsheet나 drawer를 제공할지는 전적으로 사용하는 사람의 몫이다. 이와 동일하게 오버레이에 대한 애니메이션 효과도 사용자에게 원하는 만큼 사용할 수 있도록 권한을 부여한다.

fade-out애니메이션이 0.1초든 10초든(그럴리는 없겠지만..) 원하는 만큼 보여줄 수 있는 선택권을 넘기기 위해 close는 언마운트 되어 메모리에서 사라지지 않는다. isOpen이 false일 때 애니메이션을 작성하면 된다. 그리고 사용자는

```javascript
useOverlay(({ isOpen , close })=><div>...</div>)
```

close를 통해 ui를 닫음으로써 애니메이션을 보여줄 수 있게 된다.

## 메모리 누수가 발생하는 것 아닌가

그럼 오버레이가 한 화면에 여러 개 사용되고, 매번 close를 사용하면 서비스가 커질수록 메모리 누수가 발생하는 것 아닌가?

위에서도 잠깐 나왔지만 사용자가 컴포넌트에서 호출하는 useOverlay훅 내부에 클린업이 있다.

```javascript
export function useOverlay() {
  ...

  useEffect(() => {
    return () => {
      if (exitOnUnmount) {
        unmount(id);
      }
    };
  }, [exitOnUnmount, id, unmount]);

  return useMemo(
    () => ({
      open: (overlayElement: CreateOverlayElement) => {
        mount(
          id,
          <OverlayController
           ...
          />
        );
      },
      close: () => {
        overlayRef.current?.close();
      },
      exit: () => {
        unmount(id);
      },
    }),
    [id, mount, unmount]
  );
}
```

id는 훅이 호출될 때마다 전역변수에서 1씩 증가하여 할당된다. 리액트 컴포넌트에서 3번 useOverlay를 호출해도 리액트 컴포넌트가 언마운트 될 때, 클린업이 동작하여 close로 열었던 모든 overlay를 청소하게 된다.

즉, 오버레이가 닫힐 때 즉시 청소되지는 않지만 화면이 사라질 때 모든 오버레이가 한꺼번에 청소되므로 큰 메모리 낭비라고 볼 수 없다.

## 커스텀 하고 싶은 두 가지

커스텀하기

내가 커스텀 하고 싶은 부분은 두 가지이다. 애니메이션이 기본으로 들어간 모달 ui를 기본으로 사용하는 훅인 useModal라는 훅을 만들어서 기본 ui로 모달을 제공한다. 두 번째는 훅 호출 인터페이스를 간소화한다.

```javascript
export const Component = () => {
	const overlay = useOverlay();

    const handleOpen = () => {
    	overlay.open(({isOpen, close})=>{
        	<Modal isOpen={isOpen} close={close}>
            	...
            </Modal>
        })
    };

    const handleOpen2 = () => {
    	overlay.open(({isOpen, close})=>{
        	<Modal isOpen={isOpen} close={close}>
            	...
            </Modal>
        })
    };

    const handleOpen3 = () => {
    	overlay.open(({isOpen, close})=>{
        	<Modal isOpen={isOpen} close={close}>
            	...
            </Modal>
        })
    };

    return (
    	...
    )
}
```

위에서 보면 모달을 호출할 때마다 당연한 isOpen, 그리고 dim영역을 클릭할 때 닫히게 하기 위한 close를 계속 전달해 줘야 한다.

모달의 기본인데, 계속 isOpen과 close를 꺼내서 전달해 주는 반복을 제거하고 싶다.

아래와 같이 변경된다.

```javascript
const overlay = useOverlay()

overlay.open(()=><Modal><div>content</div></Modal>)

overlay.open(()=><Modal><div>content</div></Modal>)

overlay.open(()=><Modal><div>content</div></Modal>)
```

두 번째로 useOverlay로 호출하고 <Modal> ui를 리턴하는 걸 매번 하는 게 아니라 useModal, useDrawer라는 훅으로 래핑 해서 애니메이션을 기본으로 주고 애니메이션이 끝나면 즉시 unmount 해서 메모리에서 바로 비우고 싶다.

아래와 같이 변경된다.

```javascript
const modal = useModal()

modal.open(()=><div>content</div>)
// 닫히면 애니메이션이 실행되고, 애니메이션이 종료되면 즉시 unmount되어 메모리가 비워진다.

const drawer = useDrawer()

drawer.open(()=><div>content</div>)
// 닫히면 애니메이션이 실행되고, 애니메이션이 종료되면 즉시 unmount되어 메모리가 비워진다.
```

## 커스텀 버전

custom version

```javascript
export const OverlayController = forwardRef(
  (
    { overlayContent: OverlayContent, id }: Props,
    ref: Ref<OverlayControlRef>
  ) => {
    const { unmount } = useOverlayContext();
    const [isOverlayOpen, setIsOverlayOpen] = useState(false);
    const [isRemoving, setIsRemoving] = useState(false);

    const handleOverlayClose = useCallback(() => {
      setIsRemoving(true);
      setTimeout(() => {
        setIsOverlayOpen(false);
        unmount(id);
      }, ANIMATION_DELAY);
    }, [id, unmount]);

    useKeyPress("Escape", handleOverlayClose);
    useImperativeHandle(ref, () => {
      return { close: handleOverlayClose };
    });

    useEffect(() => {
      requestAnimationFrame(() => {
        setIsOverlayOpen(true);
      });
    }, []);

    return (
      <OverlayContent
        isOpen={isOverlayOpen}
        isRemoving={isRemoving}
        close={handleOverlayClose}
      />
    );
  }
);
OverlayController.displayName = "OverlayController";
```

변경 포인트: 내 커스텀 버전에서는 모달이 닫히는 애니메이션을 사용 후에 개별 모달이 닫힐때마다 기본으로 unmount 시켜서 메모리를 즉시 비워줄 것이다. 왜냐하면 나는 사용자입장이니까 어떤 애니메이션을 얼마나 사용할지 알고 있으니 괜찮다.

handleOverlayClose를 close함수로 사용자에게 제공한다. exit은 제공하지 않을 것이다. 애니메이션 꼭 보여주게 하고싶다. 실행되면 즉시 isRemoving을 true로 만들어서 애니메이션을 실행한다. 그리고 ANIMATION_DELAY가 지난 뒤에 언마운트 한다. useKeyPress훅을 만들어서 Esc키를 누르면 닫힐 수 있도록 해당 핸들러를 등록했다.

```javascript
import { Modal } from "@/overlay/Modal";
import { useOverlay } from "@/overlay/useOverlay";
import { ReactNode } from "react";

export const useModal = () => {
  const overlay = useOverlay();

  return {
    open: (content: (close: () => void) => ReactNode) => {
      overlay.open(({ isOpen, close, isRemoving }) => (
        <Modal isOpen={isOpen} close={close} isRemoving={isRemoving}>
          {content(close)}
        </Modal>
      ));
    },
    close: overlay.close,
  };
};
```

아직은 모달만 작성했는데, 추후 useDrawer, useBottomSheet도 동일하게 작성하면 된다.

useModal은 내부적으로 useOverlay를 호출하고 Modal ui에 필요한 상태를 넘겨준다.

## close는 콜백의 매개변수로

사용자에게 ReactNode타입만 입력받도록 해서 더 간단하게 사용하게 하면 어떨까 했지만 close는 사용할 수 있도록했다.

```javascript
const modal = useModal()

modal.open(<div>content</div>)
```

이렇게 하면 더 편리해 보이지만 만약 콘텐츠를 다른 파일에 작성하게 되면 해당 파일에서 close를 호출하기 좀 헷갈려질 수 있다.

왜냐하면 modal객체 자체를 props로 받아야 하기 때문에

```javascript
export const ModalContent = ({modal}) =>{
	return <div><button onClick={modal.close}>닫기
}
```

이런 식으로 사용하게 되면 이 modal이 props인지, 해당 컴포넌트 내부에서 호출한 modal인지 헷갈릴 여지가 있으므로 close함수만큼은 콜백의 매개변수로 받아서 사용할 수 있도록 하는 게 좋을 것 같다.

```javascript
  const modal = useModal();

  const openModal = () => {
    modal.open((close) => (
      <div>
        asd<button onClick={close}>close</button>
      </div>
    ));
  };
```

이제 반복해야 하는 ui를 훅 내부에서 처리하기 때문에 사용자(개발자)가 굳이 뻔하디 뻔한 상태를 매번 넘기지 않아도 된다.

해당 모달은 dim영역을 클릭해서 닫거나, esc키를 누르거나 close함수를 호출하거나 모두 내부적으로 handleOverlayClose를 호출하기 때문에 항상 애니메이션 후 언마운트 된다. 게다가 사용자 인터페이스도 더 편하다.
