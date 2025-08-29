"use client";

import { useQuery } from '@tanstack/react-query';
import { getBillingInfo, BillingInfo as BillingInfoType } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge';

// --- Mock Data ---
// In a real app, this would come from the API.
const mockBillingData = {
  plan: 'Pro',
  status: 'active',
  price: 99,
  currency: 'USD',
  next_billing_date: new Date(new Date().setMonth(new Date().getMonth() + 1)).toISOString(),
  features: [
    "10,000 monthly messages",
    "5 AI agents",
    "Advanced analytics",
    "Priority support"
  ],
  invoices: [
    { id: 'inv_1', date: new Date(new Date().setMonth(new Date().getMonth() - 1)).toISOString(), amount: 99.00, status: 'Paid' },
    { id: 'inv_2', date: new Date(new Date().setMonth(new Date().getMonth() - 2)).toISOString(), amount: 99.00, status: 'Paid' },
    { id: 'inv_3', date: new Date(new Date().setMonth(new Date().getMonth() - 3)).toISOString(), amount: 99.00, status: 'Paid' },
  ]
};

export default function BillingInfo() {
  // We keep the query to simulate a real data fetch, but we'll use mock data for the UI.
  const { isLoading, isError, error } = useQuery({
    queryKey: ['billingInfo'],
    queryFn: getBillingInfo,
  });

  if (isLoading) {
    return <p className="text-center text-gray-500">Loading billing information...</p>;
  }

  if (isError) {
    return <p className="text-center text-red-500">Error loading billing info: {error.message}</p>;
  }

  const data = mockBillingData; // Using mock data

  const statusColors: { [key: string]: string } = {
    active: 'bg-green-100 text-green-800',
    canceled: 'bg-gray-100 text-gray-800',
    past_due: 'bg-yellow-100 text-yellow-800',
  };

  return (
    <div className="space-y-8 mt-6">
      {/* Current Plan Section */}
      <Card>
        <CardHeader className="flex flex-row justify-between items-start">
          <div>
            <CardTitle>Your Current Plan</CardTitle>
            <CardDescription>
              Next bill on {new Date(data.next_billing_date).toLocaleDateString()}
            </CardDescription>
          </div>
          {/* In a real app, this would link to the Stripe Customer Portal */}
          <Button variant="outline">Manage Subscription</Button>
        </CardHeader>
        <CardContent className="grid gap-6 md:grid-cols-2">
          <div className="space-y-2">
            <h3 className="text-2xl font-bold">{data.plan} Plan</h3>
            <p className="text-3xl font-bold">
              ${data.price}<span className="text-lg font-normal text-gray-500">/month</span>
            </p>
            <Badge className={statusColors[data.status] || 'bg-gray-100'}>
              {data.status.charAt(0).toUpperCase() + data.status.slice(1)}
            </Badge>
          </div>
          <div className="space-y-3">
            <h4 className="font-semibold">What&apos;s included:</h4>
            <ul className="list-disc list-inside text-gray-600 space-y-1">
              {data.features.map((feature, i) => <li key={i}>{feature}</li>)}
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Invoice History Section */}
      <Card>
        <CardHeader>
          <CardTitle>Invoice History</CardTitle>
          <CardDescription>Your past payments and invoices.</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Invoice ID</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.invoices.map((invoice) => (
                <TableRow key={invoice.id}>
                  <TableCell className="font-mono text-xs">{invoice.id}</TableCell>
                  <TableCell>{new Date(invoice.date).toLocaleDateString()}</TableCell>
                  <TableCell>${invoice.amount.toFixed(2)}</TableCell>
                  <TableCell>
                    <Badge variant={invoice.status === 'Paid' ? 'default' : 'secondary'} className={invoice.status === 'Paid' ? 'bg-green-100 text-green-800' : ''}>
                      {invoice.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="outline" size="sm">Download</Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
