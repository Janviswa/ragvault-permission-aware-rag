import Link from "next/link";

export default function RegisterPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-6">
      <div className="panel w-full max-w-md p-10 text-center">
        <h1 className="text-xl font-bold">Accounts are created by your administrator</h1>
        <p className="mt-3 text-sm leading-6 text-graphite">Public sign-up is turned off. Ask your company administrator to add you.</p>
        <Link href="/login" className="btn-solid mt-6">Back to sign in</Link>
      </div>
    </main>
  );
}
