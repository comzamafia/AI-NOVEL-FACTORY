import { NextRequest, NextResponse } from 'next/server';

// App Router: body is raw by default in route handlers — no extra config needed
export const dynamic = 'force-dynamic';

// Stripe webhook handler
export async function POST(req: NextRequest) {
  const rawBody = await req.text();
  const signature = req.headers.get('stripe-signature') || '';
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

  if (!webhookSecret || webhookSecret.includes('your_webhook')) {
    // Demo mode
    console.log('[Webhook Demo] Received event (no secret configured)');
    return NextResponse.json({ received: true });
  }

  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const Stripe = require('stripe');
    const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
      apiVersion: '2024-04-10',
    });

    const event = stripe.webhooks.constructEvent(rawBody, signature, webhookSecret);

    // Forward event to Django backend
    const djangoWebhookUrl = `${process.env.NEXT_PUBLIC_API_URL?.replace('/api', '')}/api/webhooks/stripe/`;

    try {
      await fetch(djangoWebhookUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Stripe-Signature': signature,
        },
        body: rawBody,
      });
    } catch (forwardErr) {
      console.error('Failed to forward to Django:', forwardErr);
      // Don't fail — Stripe needs 200 back
    }

    // Handle specific events locally if needed
    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object;
        console.log('[Webhook] Checkout completed:', session.id, session.metadata);
        break;
      }
      case 'customer.subscription.updated':
      case 'customer.subscription.deleted': {
        const sub = event.data.object;
        console.log('[Webhook] Subscription change:', sub.id);
        break;
      }
      default:
        console.log('[Webhook] Unhandled event type:', event.type);
    }

    return NextResponse.json({ received: true });
  } catch (err) {
    console.error('[Webhook] Error:', err);
    return NextResponse.json({ error: 'Webhook error' }, { status: 400 });
  }
}
