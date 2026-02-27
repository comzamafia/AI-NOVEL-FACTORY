import { NextRequest, NextResponse } from 'next/server';

// NOTE: Install stripe server-side: npm install stripe
// import Stripe from 'stripe';
// const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, { apiVersion: '2024-04-10' });

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { type, chapterId, plan, successUrl, cancelUrl } = body;

    // Validate Stripe secret key is configured
    if (!process.env.STRIPE_SECRET_KEY || process.env.STRIPE_SECRET_KEY.includes('your_stripe')) {
      // Demo mode — return mock checkout URL
      return NextResponse.json({
        url: `${successUrl}&demo=1`,
        sessionId: 'demo_session_id',
      });
    }

    // Dynamic import to avoid build errors when stripe is not installed
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const Stripe = require('stripe');
    const stripe = new Stripe(process.env.STRIPE_SECRET_KEY, {
      apiVersion: '2024-04-10',
    });

    let session;

    if (type === 'chapter') {
      session = await stripe.checkout.sessions.create({
        payment_method_types: ['card'],
        mode: 'payment',
        line_items: [
          {
            price_data: {
              currency: 'usd',
              unit_amount: 199, // $1.99
              product_data: {
                name: `Chapter ${chapterId} — Single Purchase`,
                description: 'One-time purchase to unlock this chapter forever.',
              },
            },
            quantity: 1,
          },
        ],
        metadata: {
          type: 'chapter',
          chapter_id: String(chapterId),
        },
        success_url: successUrl,
        cancel_url: cancelUrl,
      });
    } else if (type === 'subscription') {
      // You need to create a price in Stripe dashboard and set the price ID here
      const priceId =
        plan === 'annual'
          ? process.env.STRIPE_PRICE_ANNUAL_ID || ''
          : process.env.STRIPE_PRICE_MONTHLY_ID || '';

      session = await stripe.checkout.sessions.create({
        payment_method_types: ['card'],
        mode: 'subscription',
        line_items: [
          {
            price: priceId || undefined,
            // Fallback if no price ID configured
            ...(priceId
              ? {}
              : {
                  price_data: {
                    currency: 'usd',
                    unit_amount: plan === 'annual' ? 7999 : 999,
                    recurring: { interval: plan === 'annual' ? 'year' : 'month' },
                    product_data: {
                      name: 'NovelFactory Subscription',
                      description: 'Unlimited access to all books and chapters.',
                    },
                  },
                }),
            quantity: 1,
          },
        ],
        metadata: {
          type: 'subscription',
          plan: plan || 'monthly',
        },
        success_url: successUrl,
        cancel_url: cancelUrl,
      });
    } else {
      return NextResponse.json({ error: 'Invalid checkout type' }, { status: 400 });
    }

    return NextResponse.json({ url: session.url, sessionId: session.id });
  } catch (err: unknown) {
    console.error('Stripe checkout error:', err);
    const message = err instanceof Error ? err.message : 'Internal server error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
