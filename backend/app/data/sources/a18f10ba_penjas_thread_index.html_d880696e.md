# Attempt to read property "judul" on null (View: /usr/local/www/kdsumedang/resources/views/penjas/thread.blade.php) (500 Internal Server Error)

> Source: https://kd-sumedang.upi.edu/penjas/thread/index.html

Symfony Exception
Source: penjas_thread_index.html_d880696e.html
Symfony Exception
Symfony Docs
ErrorExceptionViewException
HTTP 500 Internal Server Error
Attempt to read property "judul" on null (View: /usr/local/www/kdsumedang/resources/views/penjas/thread.blade.php)
Exceptions 2Stack Traces 2
Exceptions 2
Illuminate\View\ ViewException
Show exception properties
in /usr/local/www/kdsumedang/storage/framework/views/e4bce5ecc273f2745c6fdcd2b5ec0cad.php (line 4)
<!DOCTYPE html>
<html>
<head>
    <title><?php echo e($beritapenjas->judul); ?></title>
</head>
<body>
    
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/Engines/PhpEngine.php->handleViewException (line 60)
        // flush out any stray output that might get out before an error occurs or
        // an exception is thrown. This prevents any partial views from leaking.
        try {
            $this->files->getRequire($path, $data);
        } catch (Throwable $e) {
            $this->handleViewException($e, $obLevel);
        }
        return ltrim(ob_get_clean());
    }
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/Engines/CompilerEngine.php->evaluatePath (line 72)
        // Once we have the path to the compiled file, we will evaluate the paths with
        // typical PHP just like any other templates. We also keep a stack of views
        // which have been rendered for right exception messages to be generated.
        try {
            $results = $this->evaluatePath($this->compiler->getCompiledPath($path), $data);
        } catch (ViewException $e) {
            if (! str($e->getMessage())->contains(['No such file or directory', 'File does not exist at path'])) {
                throw $e;
            }
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/View.php->get (line 207)
     *
     * @return string
     */
    protected function getContents()
    {
        return $this->engine->get($this->path, $this->gatherData());
    }
    /**
     * Get the data bound to the view instance.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/View.php->getContents (line 190)
        // clear out the sections for any separate views that may be rendered.
        $this->factory->incrementRender();
        $this->factory->callComposer($this);
        $contents = $this->getContents();
        // Once we've finished rendering the view, we'll decrement the render count
        // so that each section gets flushed out next time a view is created and
        // no old sections are staying around in the memory of an environment.
        $this->factory->decrementRender();
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/View.php->renderContents (line 159)
     * @throws \Throwable
     */
    public function render(callable $callback = null)
    {
        try {
            $contents = $this->renderContents();
            $response = isset($callback) ? $callback($this, $contents) : null;
            // Once we have the contents of the view, we will flush the sections if we are
            // done rendering all views so that there is nothing left hanging over when
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Http/Response.php->render (line 69)
        // If this content implements the "Renderable" interface then we will call the
        // render method on the object so we will avoid any "__toString" exceptions
        // that might be thrown and have their errors obscured by PHP's handling.
        elseif ($content instanceof Renderable) {
            $content = $content->render();
        }
        parent::setContent($content);
        return $this;
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Http/Response.php->setContent (line 35)
     */
    public function __construct($content = '', $status = 200, array $headers = [])
    {
        $this->headers = new ResponseHeaderBag($headers);
        $this->setContent($content);
        $this->setStatusCode($status);
        $this->setProtocolVersion('1.0');
    }
    /**
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php->__construct (line 918)
                    $response instanceof JsonSerializable ||
                    $response instanceof stdClass ||
                    is_array($response))) {
            $response = new JsonResponse($response);
        } elseif (! $response instanceof SymfonyResponse) {
            $response = new Response($response, 200, ['Content-Type' => 'text/html']);
        }
        if ($response->getStatusCode() === Response::HTTP_NOT_MODIFIED) {
            $response->setNotModified();
        }
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php::toResponse (line 885)
     */
    public function prepareResponse($request, $response)
    {
        $this->events->dispatch(new PreparingResponse($request, $response));
        return tap(static::toResponse($request, $response), function ($response) use ($request) {
            $this->events->dispatch(new ResponsePrepared($request, $response));
        });
    }
    /**
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php->prepareResponse (line 805)
        $middleware = $shouldSkipMiddleware ? [] : $this->gatherRouteMiddleware($route);
        return (new Pipeline($this->container))
                        ->send($request)
                        ->through($middleware)
                        ->then(fn ($request) => $this->prepareResponse(
                            $request, $route->run()
                        ));
    }
    /**
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->{closure:Illuminate\Routing\Router::runRouteWithinStack():805} (line 144)
     */
    protected function prepareDestination(Closure $destination)
    {
        return function ($passable) use ($destination) {
            try {
                return $destination($passable);
            } catch (Throwable $e) {
                return $this->handleException($passable, $e);
            }
        };
    }
Pipeline->{closure:Illuminate\Pipeline\Pipeline::prepareDestination():142}() in /usr/local/www/kdsumedang/app/Http/Middleware/MinifyHtml.php (line 18)
     *
     * @param  \Closure(\Illuminate\Http\Request): (\Symfony\Component\HttpFoundation\Response)  $next
     */
     public function handle($request, Closure $next)
    {
        $response = $next($request);
        if (
            $response instanceof \Illuminate\Http\Response &&
            strpos($response->headers->get('Content-Type'), 'text/html') !== false
        ) {
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Middleware/SubstituteBindings.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 50)
            }
            throw $exception;
        }
        return $next($request);
    }
}
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/VerifyCsrfToken.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 78)
            $this->isReading($request) ||
            $this->runningUnitTests() ||
            $this->inExceptArray($request) ||
            $this->tokensMatch($request)
        ) {
            return tap($next($request), function ($response) use ($request) {
                if ($this->shouldAddXsrfTokenCookie()) {
                    $this->addCookieToResponse($request, $response);
                }
            });
        }
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/Middleware/ShareErrorsFromSession.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 49)
        // Putting the errors in the view for every view allows the developer to just
        // assume that some errors are always available, which is convenient since
        // they don't have to continually run checks for the presence of errors.
        return $next($request);
    }
}
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Session/Middleware/StartSession.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 121)
            $this->startSession($request, $session)
        );
        $this->collectGarbage($session);
        $response = $next($request);
        $this->storeCurrentUrl($request, $session);
        $this->addCookieToResponse($response, $session);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Session/Middleware/StartSession.php->handleStatefulRequest (line 64)
        if ($this->manager->shouldBlock() ||
            ($request->route() instanceof Route && $request->route()->locksFor())) {
            return $this->handleRequestWhileBlocking($request, $session, $next);
        }
        return $this->handleStatefulRequest($request, $session, $next);
    }
    /**
     * Handle the given request within session state.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Cookie/Middleware/AddQueuedCookiesToResponse.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 37)
     * @param  \Closure  $next
     * @return mixed
     */
    public function handle($request, Closure $next)
    {
        $response = $next($request);
        foreach ($this->cookies->getQueuedCookies() as $cookie) {
            $response->headers->setCookie($cookie);
        }
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Cookie/Middleware/EncryptCookies.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 67)
     * @param  \Closure  $next
     * @return \Symfony\Component\HttpFoundation\Response
     */
    public function handle($request, Closure $next)
    {
        return $this->encrypt($next($this->decrypt($request)));
    }
    /**
     * Decrypt the cookies on the request.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 119)
    {
        $pipeline = array_reduce(
            array_reverse($this->pipes()), $this->carry(), $this->prepareDestination($destination)
        );
        return $pipeline($this->passable);
    }
    /**
     * Run the pipeline and return the result.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php->then (line 805)
        $middleware = $shouldSkipMiddleware ? [] : $this->gatherRouteMiddleware($route);
        return (new Pipeline($this->container))
                        ->send($request)
                        ->through($middleware)
                        ->then(fn ($request) => $this->prepareResponse(
                            $request, $route->run()
                        ));
    }
    /**
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php->runRouteWithinStack (line 784)
        $request->setRouteResolver(fn () => $route);
        $this->events->dispatch(new RouteMatched($route, $request));
        return $this->prepareResponse($request,
            $this->runRouteWithinStack($route, $request)
        );
    }
    /**
     * Run the given route within a Stack "onion" instance.
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php->runRoute (line 748)
     * @param  \Illuminate\Http\Request  $request
     * @return \Symfony\Component\HttpFoundation\Response
     */
    public function dispatchToRoute(Request $request)
    {
        return $this->runRoute($request, $this->findRoute($request));
    }
    /**
     * Find the route matching a given request.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php->dispatchToRoute (line 737)
     */
    public function dispatch(Request $request)
    {
        $this->currentRequest = $request;
        return $this->dispatchToRoute($request);
    }
    /**
     * Dispatch the request to a route and return the response.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Kernel.php->dispatch (line 200)
    protected function dispatchToRouter()
    {
        return function ($request) {
            $this->app->instance('request', $request);
            return $this->router->dispatch($request);
        };
    }
    /**
     * Call the terminate method on any terminable middleware.
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->{closure:Illuminate\Foundation\Http\Kernel::dispatchToRouter():197} (line 144)
     */
    protected function prepareDestination(Closure $destination)
    {
        return function ($passable) use ($destination) {
            try {
                return $destination($passable);
            } catch (Throwable $e) {
                return $this->handleException($passable, $e);
            }
        };
    }
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/TransformsRequest.php->{closure:Illuminate\Pipeline\Pipeline::prepareDestination():142} (line 21)
     */
    public function handle($request, Closure $next)
    {
        $this->clean($request);
        return $next($request);
    }
    /**
     * Clean the request's data.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/ConvertEmptyStringsToNull.php->handle (line 31)
            if ($callback($request)) {
                return $next($request);
            }
        }
        return parent::handle($request, $next);
    }
    /**
     * Transform the given value.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/TransformsRequest.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 21)
     */
    public function handle($request, Closure $next)
    {
        $this->clean($request);
        return $next($request);
    }
    /**
     * Clean the request's data.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/TrimStrings.php->handle (line 40)
            if ($callback($request)) {
                return $next($request);
            }
        }
        return parent::handle($request, $next);
    }
    /**
     * Transform the given value.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/ValidatePostSize.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 27)
        if ($max > 0 && $request->server('CONTENT_LENGTH') > $max) {
            throw new PostTooLargeException;
        }
        return $next($request);
    }
    /**
     * Determine the server 'post_max_size' as bytes.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/PreventRequestsDuringMaintenance.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 99)
                null,
                $this->getHeaders($data)
            );
        }
        return $next($request);
    }
    /**
     * Determine if the incoming request has a maintenance mode bypass cookie.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Http/Middleware/HandleCors.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 49)
     * @return \Illuminate\Http\Response
     */
    public function handle($request, Closure $next)
    {
        if (! $this->hasMatchingPath($request)) {
            return $next($request);
        }
        $this->cors->setOptions($this->container['config']->get('cors', []));
        if ($this->cors->isPreflightRequest($request)) {
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Http/Middleware/TrustProxies.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 39)
    {
        $request::setTrustedProxies([], $this->getTrustedHeaderNames());
        $this->setTrustedProxyIpAddresses($request);
        return $next($request);
    }
    /**
     * Sets the trusted proxies on the request.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 119)
    {
        $pipeline = array_reduce(
            array_reverse($this->pipes()), $this->carry(), $this->prepareDestination($destination)
        );
        return $pipeline($this->passable);
    }
    /**
     * Run the pipeline and return the result.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Kernel.php->then (line 175)
        $this->bootstrap();
        return (new Pipeline($this->app))
                    ->send($request)
                    ->through($this->app->shouldSkipMiddleware() ? [] : $this->middleware)
                    ->then($this->dispatchToRouter());
    }
    /**
     * Bootstrap the application for HTTP requests.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Kernel.php->sendRequestThroughRouter (line 144)
        $this->requestStartedAt = Carbon::now();
        try {
            $request->enableHttpMethodParameterOverride();
            $response = $this->sendRequestThroughRouter($request);
        } catch (Throwable $e) {
            $this->reportException($e);
            $response = $this->renderException($request, $e);
        }
Kernel->handle() in /usr/local/www/kdsumedang/public/index.php (line 51)
$app = require_once __DIR__.'/../bootstrap/app.php';
$kernel = $app->make(Kernel::class);
$response = $kernel->handle(
    $request = Request::capture()
)->send();
$kernel->terminate($request, $response);
ErrorException

Attempt to read property "judul" on null

in /usr/local/www/kdsumedang/storage/framework/views/e4bce5ecc273f2745c6fdcd2b5ec0cad.php (line 4)
<!DOCTYPE html>
<html>
<head>
    <title><?php echo e($beritapenjas->judul); ?></title>
</head>
<body>
    
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Bootstrap/HandleExceptions.php->handleError (line 255)
     * @return callable
     */
    protected function forwardsTo($method)
    {
        return fn (...$arguments) => static::$app
            ? $this->{$method}(...$arguments)
            : false;
    }
    /**
     * Determine if the error level is a deprecation.
HandleExceptions->{closure:Illuminate\Foundation\Bootstrap\HandleExceptions::forwardsTo():254}() in /usr/local/www/kdsumedang/storage/framework/views/e4bce5ecc273f2745c6fdcd2b5ec0cad.php (line 4)
<!DOCTYPE html>
<html>
<head>
    <title><?php echo e($beritapenjas->judul); ?></title>
</head>
<body>
    
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Filesystem/Filesystem.phprequire (line 123)
            $__data = $data;
            return (static function () use ($__path, $__data) {
                extract($__data, EXTR_SKIP);
                return require $__path;
            })();
        }
        throw new FileNotFoundException("File does not exist at path {$path}.");
    }
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Filesystem/Filesystem.php::{closure:Illuminate\Filesystem\Filesystem::getRequire():120} (line 124)
            return (static function () use ($__path, $__data) {
                extract($__data, EXTR_SKIP);
                return require $__path;
            })();
        }
        throw new FileNotFoundException("File does not exist at path {$path}.");
    }
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/Engines/PhpEngine.php->getRequire (line 58)
        // We'll evaluate the contents of the view inside a try/catch block so we can
        // flush out any stray output that might get out before an error occurs or
        // an exception is thrown. This prevents any partial views from leaking.
        try {
            $this->files->getRequire($path, $data);
        } catch (Throwable $e) {
            $this->handleViewException($e, $obLevel);
        }
        return ltrim(ob_get_clean());
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/Engines/CompilerEngine.php->evaluatePath (line 72)
        // Once we have the path to the compiled file, we will evaluate the paths with
        // typical PHP just like any other templates. We also keep a stack of views
        // which have been rendered for right exception messages to be generated.
        try {
            $results = $this->evaluatePath($this->compiler->getCompiledPath($path), $data);
        } catch (ViewException $e) {
            if (! str($e->getMessage())->contains(['No such file or directory', 'File does not exist at path'])) {
                throw $e;
            }
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/View.php->get (line 207)
     *
     * @return string
     */
    protected function getContents()
    {
        return $this->engine->get($this->path, $this->gatherData());
    }
    /**
     * Get the data bound to the view instance.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/View.php->getContents (line 190)
        // clear out the sections for any separate views that may be rendered.
        $this->factory->incrementRender();
        $this->factory->callComposer($this);
        $contents = $this->getContents();
        // Once we've finished rendering the view, we'll decrement the render count
        // so that each section gets flushed out next time a view is created and
        // no old sections are staying around in the memory of an environment.
        $this->factory->decrementRender();
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/View.php->renderContents (line 159)
     * @throws \Throwable
     */
    public function render(callable $callback = null)
    {
        try {
            $contents = $this->renderContents();
            $response = isset($callback) ? $callback($this, $contents) : null;
            // Once we have the contents of the view, we will flush the sections if we are
            // done rendering all views so that there is nothing left hanging over when
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Http/Response.php->render (line 69)
        // If this content implements the "Renderable" interface then we will call the
        // render method on the object so we will avoid any "__toString" exceptions
        // that might be thrown and have their errors obscured by PHP's handling.
        elseif ($content instanceof Renderable) {
            $content = $content->render();
        }
        parent::setContent($content);
        return $this;
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Http/Response.php->setContent (line 35)
     */
    public function __construct($content = '', $status = 200, array $headers = [])
    {
        $this->headers = new ResponseHeaderBag($headers);
        $this->setContent($content);
        $this->setStatusCode($status);
        $this->setProtocolVersion('1.0');
    }
    /**
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php->__construct (line 918)
                    $response instanceof JsonSerializable ||
                    $response instanceof stdClass ||
                    is_array($response))) {
            $response = new JsonResponse($response);
        } elseif (! $response instanceof SymfonyResponse) {
            $response = new Response($response, 200, ['Content-Type' => 'text/html']);
        }
        if ($response->getStatusCode() === Response::HTTP_NOT_MODIFIED) {
            $response->setNotModified();
        }
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php::toResponse (line 885)
     */
    public function prepareResponse($request, $response)
    {
        $this->events->dispatch(new PreparingResponse($request, $response));
        return tap(static::toResponse($request, $response), function ($response) use ($request) {
            $this->events->dispatch(new ResponsePrepared($request, $response));
        });
    }
    /**
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php->prepareResponse (line 805)
        $middleware = $shouldSkipMiddleware ? [] : $this->gatherRouteMiddleware($route);
        return (new Pipeline($this->container))
                        ->send($request)
                        ->through($middleware)
                        ->then(fn ($request) => $this->prepareResponse(
                            $request, $route->run()
                        ));
    }
    /**
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->{closure:Illuminate\Routing\Router::runRouteWithinStack():805} (line 144)
     */
    protected function prepareDestination(Closure $destination)
    {
        return function ($passable) use ($destination) {
            try {
                return $destination($passable);
            } catch (Throwable $e) {
                return $this->handleException($passable, $e);
            }
        };
    }
Pipeline->{closure:Illuminate\Pipeline\Pipeline::prepareDestination():142}() in /usr/local/www/kdsumedang/app/Http/Middleware/MinifyHtml.php (line 18)
     *
     * @param  \Closure(\Illuminate\Http\Request): (\Symfony\Component\HttpFoundation\Response)  $next
     */
     public function handle($request, Closure $next)
    {
        $response = $next($request);
        if (
            $response instanceof \Illuminate\Http\Response &&
            strpos($response->headers->get('Content-Type'), 'text/html') !== false
        ) {
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Middleware/SubstituteBindings.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 50)
            }
            throw $exception;
        }
        return $next($request);
    }
}
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/VerifyCsrfToken.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 78)
            $this->isReading($request) ||
            $this->runningUnitTests() ||
            $this->inExceptArray($request) ||
            $this->tokensMatch($request)
        ) {
            return tap($next($request), function ($response) use ($request) {
                if ($this->shouldAddXsrfTokenCookie()) {
                    $this->addCookieToResponse($request, $response);
                }
            });
        }
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/Middleware/ShareErrorsFromSession.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 49)
        // Putting the errors in the view for every view allows the developer to just
        // assume that some errors are always available, which is convenient since
        // they don't have to continually run checks for the presence of errors.
        return $next($request);
    }
}
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Session/Middleware/StartSession.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 121)
            $this->startSession($request, $session)
        );
        $this->collectGarbage($session);
        $response = $next($request);
        $this->storeCurrentUrl($request, $session);
        $this->addCookieToResponse($response, $session);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Session/Middleware/StartSession.php->handleStatefulRequest (line 64)
        if ($this->manager->shouldBlock() ||
            ($request->route() instanceof Route && $request->route()->locksFor())) {
            return $this->handleRequestWhileBlocking($request, $session, $next);
        }
        return $this->handleStatefulRequest($request, $session, $next);
    }
    /**
     * Handle the given request within session state.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Cookie/Middleware/AddQueuedCookiesToResponse.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 37)
     * @param  \Closure  $next
     * @return mixed
     */
    public function handle($request, Closure $next)
    {
        $response = $next($request);
        foreach ($this->cookies->getQueuedCookies() as $cookie) {
            $response->headers->setCookie($cookie);
        }
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Cookie/Middleware/EncryptCookies.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 67)
     * @param  \Closure  $next
     * @return \Symfony\Component\HttpFoundation\Response
     */
    public function handle($request, Closure $next)
    {
        return $this->encrypt($next($this->decrypt($request)));
    }
    /**
     * Decrypt the cookies on the request.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 119)
    {
        $pipeline = array_reduce(
            array_reverse($this->pipes()), $this->carry(), $this->prepareDestination($destination)
        );
        return $pipeline($this->passable);
    }
    /**
     * Run the pipeline and return the result.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php->then (line 805)
        $middleware = $shouldSkipMiddleware ? [] : $this->gatherRouteMiddleware($route);
        return (new Pipeline($this->container))
                        ->send($request)
                        ->through($middleware)
                        ->then(fn ($request) => $this->prepareResponse(
                            $request, $route->run()
                        ));
    }
    /**
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php->runRouteWithinStack (line 784)
        $request->setRouteResolver(fn () => $route);
        $this->events->dispatch(new RouteMatched($route, $request));
        return $this->prepareResponse($request,
            $this->runRouteWithinStack($route, $request)
        );
    }
    /**
     * Run the given route within a Stack "onion" instance.
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php->runRoute (line 748)
     * @param  \Illuminate\Http\Request  $request
     * @return \Symfony\Component\HttpFoundation\Response
     */
    public function dispatchToRoute(Request $request)
    {
        return $this->runRoute($request, $this->findRoute($request));
    }
    /**
     * Find the route matching a given request.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php->dispatchToRoute (line 737)
     */
    public function dispatch(Request $request)
    {
        $this->currentRequest = $request;
        return $this->dispatchToRoute($request);
    }
    /**
     * Dispatch the request to a route and return the response.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Kernel.php->dispatch (line 200)
    protected function dispatchToRouter()
    {
        return function ($request) {
            $this->app->instance('request', $request);
            return $this->router->dispatch($request);
        };
    }
    /**
     * Call the terminate method on any terminable middleware.
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->{closure:Illuminate\Foundation\Http\Kernel::dispatchToRouter():197} (line 144)
     */
    protected function prepareDestination(Closure $destination)
    {
        return function ($passable) use ($destination) {
            try {
                return $destination($passable);
            } catch (Throwable $e) {
                return $this->handleException($passable, $e);
            }
        };
    }
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/TransformsRequest.php->{closure:Illuminate\Pipeline\Pipeline::prepareDestination():142} (line 21)
     */
    public function handle($request, Closure $next)
    {
        $this->clean($request);
        return $next($request);
    }
    /**
     * Clean the request's data.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/ConvertEmptyStringsToNull.php->handle (line 31)
            if ($callback($request)) {
                return $next($request);
            }
        }
        return parent::handle($request, $next);
    }
    /**
     * Transform the given value.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/TransformsRequest.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 21)
     */
    public function handle($request, Closure $next)
    {
        $this->clean($request);
        return $next($request);
    }
    /**
     * Clean the request's data.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/TrimStrings.php->handle (line 40)
            if ($callback($request)) {
                return $next($request);
            }
        }
        return parent::handle($request, $next);
    }
    /**
     * Transform the given value.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/ValidatePostSize.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 27)
        if ($max > 0 && $request->server('CONTENT_LENGTH') > $max) {
            throw new PostTooLargeException;
        }
        return $next($request);
    }
    /**
     * Determine the server 'post_max_size' as bytes.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/PreventRequestsDuringMaintenance.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 99)
                null,
                $this->getHeaders($data)
            );
        }
        return $next($request);
    }
    /**
     * Determine if the incoming request has a maintenance mode bypass cookie.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Http/Middleware/HandleCors.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 49)
     * @return \Illuminate\Http\Response
     */
    public function handle($request, Closure $next)
    {
        if (! $this->hasMatchingPath($request)) {
            return $next($request);
        }
        $this->cors->setOptions($this->container['config']->get('cors', []));
        if ($this->cors->isPreflightRequest($request)) {
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Http/Middleware/TrustProxies.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 39)
    {
        $request::setTrustedProxies([], $this->getTrustedHeaderNames());
        $this->setTrustedProxyIpAddresses($request);
        return $next($request);
    }
    /**
     * Sets the trusted proxies on the request.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 119)
    {
        $pipeline = array_reduce(
            array_reverse($this->pipes()), $this->carry(), $this->prepareDestination($destination)
        );
        return $pipeline($this->passable);
    }
    /**
     * Run the pipeline and return the result.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Kernel.php->then (line 175)
        $this->bootstrap();
        return (new Pipeline($this->app))
                    ->send($request)
                    ->through($this->app->shouldSkipMiddleware() ? [] : $this->middleware)
                    ->then($this->dispatchToRouter());
    }
    /**
     * Bootstrap the application for HTTP requests.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Kernel.php->sendRequestThroughRouter (line 144)
        $this->requestStartedAt = Carbon::now();
        try {
            $request->enableHttpMethodParameterOverride();
            $response = $this->sendRequestThroughRouter($request);
        } catch (Throwable $e) {
            $this->reportException($e);
            $response = $this->renderException($request, $e);
        }
Kernel->handle() in /usr/local/www/kdsumedang/public/index.php (line 51)
$app = require_once __DIR__.'/../bootstrap/app.php';
$kernel = $app->make(Kernel::class);
$response = $kernel->handle(
    $request = Request::capture()
)->send();
$kernel->terminate($request, $response);
Stack Traces 2
[2/2] ViewException

 Illuminate\View\ViewException: Attempt to read property "judul" on null (View: /usr/local/www/kdsumedang/resources/views/penjas/thread.blade.php) at /usr/local/www/kdsumedang/storage/framework/views/e4bce5ecc273f2745c6fdcd2b5ec0cad.php:4 at Illuminate\View\Engines\CompilerEngine->handleViewException() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/Engines/PhpEngine.php:60) at Illuminate\View\Engines\PhpEngine->evaluatePath() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/Engines/CompilerEngine.php:72) at Illuminate\View\Engines\CompilerEngine->get() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/View.php:207) at Illuminate\View\View->getContents() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/View.php:190) at Illuminate\View\View->renderContents() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/View.php:159) at Illuminate\View\View->render() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Http/Response.php:69) at Illuminate\Http\Response->setContent() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Http/Response.php:35) at Illuminate\Http\Response->__construct() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php:918) at Illuminate\Routing\Router::toResponse() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php:885) at Illuminate\Routing\Router->prepareResponse() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php:805) at Illuminate\Routing\Router->{closure:Illuminate\Routing\Router::runRouteWithinStack():805}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:144) at Illuminate\Pipeline\Pipeline->{closure:Illuminate\Pipeline\Pipeline::prepareDestination():142}() (/usr/local/www/kdsumedang/app/Http/Middleware/MinifyHtml.php:18) at App\Http\Middleware\MinifyHtml->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Middleware/SubstituteBindings.php:50) at Illuminate\Routing\Middleware\SubstituteBindings->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/VerifyCsrfToken.php:78) at Illuminate\Foundation\Http\Middleware\VerifyCsrfToken->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/Middleware/ShareErrorsFromSession.php:49) at Illuminate\View\Middleware\ShareErrorsFromSession->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Session/Middleware/StartSession.php:121) at Illuminate\Session\Middleware\StartSession->handleStatefulRequest() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Session/Middleware/StartSession.php:64) at Illuminate\Session\Middleware\StartSession->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Cookie/Middleware/AddQueuedCookiesToResponse.php:37) at Illuminate\Cookie\Middleware\AddQueuedCookiesToResponse->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Cookie/Middleware/EncryptCookies.php:67) at Illuminate\Cookie\Middleware\EncryptCookies->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:119) at Illuminate\Pipeline\Pipeline->then() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php:805) at Illuminate\Routing\Router->runRouteWithinStack() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php:784) at Illuminate\Routing\Router->runRoute() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php:748) at Illuminate\Routing\Router->dispatchToRoute() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php:737) at Illuminate\Routing\Router->dispatch() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Kernel.php:200) at Illuminate\Foundation\Http\Kernel->{closure:Illuminate\Foundation\Http\Kernel::dispatchToRouter():197}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:144) at Illuminate\Pipeline\Pipeline->{closure:Illuminate\Pipeline\Pipeline::prepareDestination():142}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/TransformsRequest.php:21) at Illuminate\Foundation\Http\Middleware\TransformsRequest->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/ConvertEmptyStringsToNull.php:31) at Illuminate\Foundation\Http\Middleware\ConvertEmptyStringsToNull->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/TransformsRequest.php:21) at Illuminate\Foundation\Http\Middleware\TransformsRequest->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/TrimStrings.php:40) at Illuminate\Foundation\Http\Middleware\TrimStrings->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/ValidatePostSize.php:27) at Illuminate\Foundation\Http\Middleware\ValidatePostSize->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/PreventRequestsDuringMaintenance.php:99) at Illuminate\Foundation\Http\Middleware\PreventRequestsDuringMaintenance->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Http/Middleware/HandleCors.php:49) at Illuminate\Http\Middleware\HandleCors->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Http/Middleware/TrustProxies.php:39) at Illuminate\Http\Middleware\TrustProxies->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:119) at Illuminate\Pipeline\Pipeline->then() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Kernel.php:175) at Illuminate\Foundation\Http\Kernel->sendRequestThroughRouter() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Kernel.php:144) at Illuminate\Foundation\Http\Kernel->handle() (/usr/local/www/kdsumedang/public/index.php:51) 
[1/2] ErrorException

 ErrorException: Attempt to read property "judul" on null at /usr/local/www/kdsumedang/storage/framework/views/e4bce5ecc273f2745c6fdcd2b5ec0cad.php:4 at Illuminate\Foundation\Bootstrap\HandleExceptions->handleError() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Bootstrap/HandleExceptions.php:255) at Illuminate\Foundation\Bootstrap\HandleExceptions->{closure:Illuminate\Foundation\Bootstrap\HandleExceptions::forwardsTo():254}() (/usr/local/www/kdsumedang/storage/framework/views/e4bce5ecc273f2745c6fdcd2b5ec0cad.php:4) at require('/usr/local/www/kdsumedang/storage/framework/views/e4bce5ecc273f2745c6fdcd2b5ec0cad.php') (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Filesystem/Filesystem.php:123) at Illuminate\Filesystem\Filesystem::{closure:Illuminate\Filesystem\Filesystem::getRequire():120}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Filesystem/Filesystem.php:124) at Illuminate\Filesystem\Filesystem->getRequire() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/Engines/PhpEngine.php:58) at Illuminate\View\Engines\PhpEngine->evaluatePath() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/Engines/CompilerEngine.php:72) at Illuminate\View\Engines\CompilerEngine->get() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/View.php:207) at Illuminate\View\View->getContents() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/View.php:190) at Illuminate\View\View->renderContents() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/View.php:159) at Illuminate\View\View->render() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Http/Response.php:69) at Illuminate\Http\Response->setContent() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Http/Response.php:35) at Illuminate\Http\Response->__construct() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php:918) at Illuminate\Routing\Router::toResponse() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php:885) at Illuminate\Routing\Router->prepareResponse() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php:805) at Illuminate\Routing\Router->{closure:Illuminate\Routing\Router::runRouteWithinStack():805}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:144) at Illuminate\Pipeline\Pipeline->{closure:Illuminate\Pipeline\Pipeline::prepareDestination():142}() (/usr/local/www/kdsumedang/app/Http/Middleware/MinifyHtml.php:18) at App\Http\Middleware\MinifyHtml->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Middleware/SubstituteBindings.php:50) at Illuminate\Routing\Middleware\SubstituteBindings->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/VerifyCsrfToken.php:78) at Illuminate\Foundation\Http\Middleware\VerifyCsrfToken->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/Middleware/ShareErrorsFromSession.php:49) at Illuminate\View\Middleware\ShareErrorsFromSession->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Session/Middleware/StartSession.php:121) at Illuminate\Session\Middleware\StartSession->handleStatefulRequest() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Session/Middleware/StartSession.php:64) at Illuminate\Session\Middleware\StartSession->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Cookie/Middleware/AddQueuedCookiesToResponse.php:37) at Illuminate\Cookie\Middleware\AddQueuedCookiesToResponse->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Cookie/Middleware/EncryptCookies.php:67) at Illuminate\Cookie\Middleware\EncryptCookies->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:119) at Illuminate\Pipeline\Pipeline->then() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php:805) at Illuminate\Routing\Router->runRouteWithinStack() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php:784) at Illuminate\Routing\Router->runRoute() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php:748) at Illuminate\Routing\Router->dispatchToRoute() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php:737) at Illuminate\Routing\Router->dispatch() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Kernel.php:200) at Illuminate\Foundation\Http\Kernel->{closure:Illuminate\Foundation\Http\Kernel::dispatchToRouter():197}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:144) at Illuminate\Pipeline\Pipeline->{closure:Illuminate\Pipeline\Pipeline::prepareDestination():142}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/TransformsRequest.php:21) at Illuminate\Foundation\Http\Middleware\TransformsRequest->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/ConvertEmptyStringsToNull.php:31) at Illuminate\Foundation\Http\Middleware\ConvertEmptyStringsToNull->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/TransformsRequest.php:21) at Illuminate\Foundation\Http\Middleware\TransformsRequest->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/TrimStrings.php:40) at Illuminate\Foundation\Http\Middleware\TrimStrings->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/ValidatePostSize.php:27) at Illuminate\Foundation\Http\Middleware\ValidatePostSize->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/PreventRequestsDuringMaintenance.php:99) at Illuminate\Foundation\Http\Middleware\PreventRequestsDuringMaintenance->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Http/Middleware/HandleCors.php:49) at Illuminate\Http\Middleware\HandleCors->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Http/Middleware/TrustProxies.php:39) at Illuminate\Http\Middleware\TrustProxies->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:119) at Illuminate\Pipeline\Pipeline->then() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Kernel.php:175) at Illuminate\Foundation\Http\Kernel->sendRequestThroughRouter() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Kernel.php:144) at Illuminate\Foundation\Http\Kernel->handle() (/usr/local/www/kdsumedang/public/index.php:51)
