# 🦁 NestJS Enterprise Architecture Guide (`nestjs.md`)

> **Framework**: NestJS (TypeScript / Node.js)  
> **Classification**: Enterprise Modular Backend Architecture  
> **Core Philosophy**: "Modular Domain Isolation, Inversion of Control, and Layered Security Guards."

---

## 1. Domain Module Anatomy

A scalable NestJS project is structured into self-contained domain feature modules:

```
src/modules/orders/
├── dto/
│   ├── create-order.dto.ts
│   └── order-response.dto.ts
├── entities/
│   └── order.entity.ts
├── guards/
│   └── order-owner.guard.ts
├── orders.controller.ts
├── orders.service.ts
└── orders.module.ts
```

---

## 2. DTO Validation & Transformation

Enforce validation globally in `main.ts`:

```typescript
// main.ts
import { ValidationPipe } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,              // Strip properties that do not have decorators
      forbidNonWhitelisted: true,   // Throw error if unknown fields are sent
      transform: true,              // Automatically transform payloads to DTO instances
      transformOptions: {
        enableImplicitConversion: false,
      },
    })
  );

  await app.listen(3000);
}
bootstrap();
```

### Strict DTO Definition
```typescript
// dto/create-order.dto.ts
import { IsArray, IsNotEmpty, IsNumber, IsPositive, IsUUID, ValidateNested } from 'class-validator';
import { Type } from 'class-transformer';

export class OrderItemDto {
  @IsUUID('4')
  @IsNotEmpty()
  productId: string;

  @IsNumber()
  @IsPositive()
  quantity: number;
}

export class CreateOrderDto {
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => OrderItemDto)
  items: OrderItemDto[];
}
```

---

## 3. JWT Authentication & Role Guards

```typescript
// guards/roles.guard.ts
import { Injectable, CanActivate, ExecutionContext, ForbiddenException } from '@nestjs/common';
import { Reflector } from '@nestjs/core';

@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredRoles = this.reflector.get<string[]>('roles', context.getHandler());
    if (!requiredRoles) return true;

    const request = context.switchToHttp().getRequest();
    const user = request.user;

    if (!user || !user.roles?.some((role: string) => requiredRoles.includes(role))) {
      throw new ForbiddenException('Insufficient role permissions');
    }
    return true;
  }
}
```

---

## 4. Global Exception Filter

```typescript
// filters/http-exception.filter.ts
import { ExceptionFilter, Catch, ArgumentsHost, HttpException, HttpStatus } from '@nestjs/common';
import { Request, Response } from 'express';

@Catch()
export class GlobalHttpExceptionFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    const status =
      exception instanceof HttpException
        ? exception.getStatus()
        : HttpStatus.INTERNAL_SERVER_ERROR;

    const message =
      exception instanceof HttpException
        ? exception.getResponse()
        : 'Internal server error';

    response.status(status).json({
      statusCode: status,
      timestamp: new Date().toISOString(),
      path: request.url,
      error: typeof message === 'string' ? message : (message as any).message || message,
    });
  }
}
```
